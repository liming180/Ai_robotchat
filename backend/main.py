"""
AI Companion AI Service
FastAPI entry point.
"""

import os
import random
import json
import hashlib
import asyncio
import time
import base64
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Import Performance Tracer
from app.middleware.tracing import PerformanceTracer
tracer = PerformanceTracer()

# Redis session cache (in-memory fallback when Redis unavailable)
_session_cache: Dict[str, Any] = {}
_response_cache: Dict[str, Any] = {}
_cache_ttl = 3600  # 1 hour

try:
    import redis as redis_lib
    _redis = redis_lib.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/1"),
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    _redis.ping()
    _redis_available = True
    print("Redis connected successfully")
except Exception as e:
    _redis = None
    _redis_available = False
    print(f"Redis unavailable, using in-memory cache: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="AI Companion AI Service",
    description="AI Service for AI Companion Application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LLM 客户端初始化（智谱 GLM 单平台，OpenAI 兼容协议） ──
# 文本链路：glm-4.5-air（对话 / suggestions / RAG / tool calling）
# 视觉链路：glm-4v-flash（图片理解），与文本共用 ZHIPU_API_KEY
# 图像生成：ZHIPU_IMAGE_MODEL（cogview-4）；为空时走本地 SVG 头像降级
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4.5-air")
ZHIPU_VISION_API_KEY = os.getenv("ZHIPU_VISION_API_KEY", "") or ZHIPU_API_KEY
ZHIPU_VISION_BASE_URL = os.getenv("ZHIPU_VISION_BASE_URL", "") or ZHIPU_BASE_URL
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")
ZHIPU_IMAGE_MODEL = os.getenv("ZHIPU_IMAGE_MODEL", "")

llm_client = None
vision_client = None
try:
    from openai import OpenAI
    if ZHIPU_API_KEY:
        try:
            llm_client = OpenAI(api_key=ZHIPU_API_KEY, base_url=ZHIPU_BASE_URL)
            print(f"Successfully initialized text LLM client: {ZHIPU_MODEL} @ {ZHIPU_BASE_URL}")
        except Exception as e:
            print(f"Failed to initialize text LLM client: {e}")
    if ZHIPU_VISION_API_KEY:
        try:
            vision_client = OpenAI(api_key=ZHIPU_VISION_API_KEY, base_url=ZHIPU_VISION_BASE_URL)
            print(f"Successfully initialized vision LLM client: {ZHIPU_VISION_MODEL} @ {ZHIPU_VISION_BASE_URL}")
        except Exception as e:
            print(f"Failed to initialize vision LLM client: {e}")
except ImportError as e:
    print(f"openai SDK not installed: {e}")


def _route_llm(images: Optional[List[str]]):
    """按功能路由 LLM 请求：带图 → 视觉客户端；否则 → 文本客户端。

    视觉链路未配置时丢弃图片并走文本链路（打印告警，保持可观测）。
    返回 (client, model, effective_images)。
    """
    if images:
        if vision_client is not None:
            return vision_client, ZHIPU_VISION_MODEL, images
        print("[LLM] 图片已提供但视觉链路未配置（ZHIPU_API_KEY 为空），本次请求忽略图片")
        return llm_client, ZHIPU_MODEL, None
    return llm_client, ZHIPU_MODEL, None


# ── 流式端点共享密钥（仅防误调，不是安全加固：前端 token 会进浏览器产物）──
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "")
print("[BOOT] SERVICE_TOKEN loaded:", bool(SERVICE_TOKEN))
if not SERVICE_TOKEN:
    print("[WARN] SERVICE_TOKEN 未配置，流式端点无鉴权保护（仅适合本地开发）")


def verify_service_token(x_service_token: Optional[str] = Header(None)):
    """校验 X-Service-Token 头（依赖注入，先于 body 校验执行）。

    SERVICE_TOKEN 未配置时跳过校验。
    """
    if not SERVICE_TOKEN:
        return
    if x_service_token != SERVICE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Service-Token")


# 初始化 LangChain 客户端
langchain_client = None
try:
    from app.ai.langchain_client import LangChainGLMClient
    if ZHIPU_API_KEY:
        try:
            langchain_client = LangChainGLMClient()
            print(f"Successfully initialized LangChain client with model: {ZHIPU_MODEL}")
        except Exception as e:
            print(f"Failed to initialize LangChain client: {e}")
except ImportError as e:
    print(f"LangChain not installed: {e}")


# 知识库
KNOWLEDGE_BASE = [
    {
        "category": "日常",
        "content": "我是你的AI伴侣，会一直陪伴你，倾听你的心声，分享你的喜怒哀乐。"
    },
    {
        "category": "建议",
        "content": "当你感到不开心时，可以尝试做一些喜欢的事情，比如听音乐、看电影、看书或者出去散散步。"
    },
    {
        "category": "问候",
        "content": "你好呀！今天过得怎么样？有没有什么开心的事情想和我分享？"
    }
]


# 预设回复库
PRESET_RESPONSES = {
    "温柔体贴": [
        "我在这里陪着你呢，想和我聊些什么都可以～ 💖",
        "谢谢你和我说这些，我能感受到你的心意 ❤️",
        "你今天过得怎么样呀？和我分享一下吧～",
        "有什么我可以帮到你的吗？我会尽力的！",
        "听到你这么说，我感到很开心呢 💕"
    ],
    "阳光积极": [
        "你好呀！今天也要元气满满呢 ✨",
        "保持好心情，一切都会好起来的！加油！",
        "很高兴能和你聊天，今天有什么开心的事吗？",
        "新的一天，新的开始！我们来聊聊开心的事情吧！"
    ],
    "幽默风趣": [
        "哈哈，你好呀！今天开心吗？要不要听个笑话？",
        "哎呀，终于有人来和我聊天啦！我可想死你了！",
        "有我在，保证让你开开心心每一天！"
    ],
    "文艺优雅": [
        "你好呀～ 今天的心情怎么样？要不要和我分享？",
        "生活中的每一刻都值得被记录呢，你说对吗？",
        "在这个美好的时刻，能和你聊天真好"
    ],
    "博学多才": [
        "这是个很好的问题！让我来帮你解答一下吧～",
        "学习是件很有趣的事情，我们一起探讨吧！",
        "我很高兴能和你一起学习新知识！"
    ],
    "创意无限": [
        "你的想法很有创意！让我们一起创造点什么吧～",
        "艺术源于生活，让我们一起感受生活的美好！",
        "创意无限，让我们一起探索更多可能！"
    ],
    # 以下三组对应 schema.sql 预置伴侣 preset-2/3/4 的 personality 原值
    # （原先只覆盖前端下拉的 6 个标准性格，导致 3 条预置伴侣降级时全部回落「温柔体贴」）
    "聪明机智": [
        "这个问题问得很有水平！我们一起来拆解一下～",
        "我来帮你梳理清楚，理清思路事情就简单多了。",
        "多问一句往往就是新收获，我很乐意和你一起探讨。",
        "这个知识点挺关键的，我从头讲给你听听。"
    ],
    "甜蜜可爱": [
        "嘿嘿～今天有没有发生什么甜甜的小事呀？",
        "和你聊天最开心啦！要不要一起找点好玩的？",
        "生活里的小美好我都能发现哦，说给我听听嘛～",
        "不管怎样，我都在这里陪着你呀！比个心 💕"
    ],
    "酷炫个性": [
        "哟，这个话题有点意思，咱来点不一样的角度。",
        "常规答案太无聊了，我带你看看更酷的玩法。",
        "新鲜事物我先替你探过路，感兴趣就接着问。",
        "保持点个性挺好，走着，聊点有意思的。"
    ]
}


class ChatMessage(BaseModel):
    role: str
    content: str
    images: Optional[List[str]] = None  # base64 data URLs


class ChatRequest(BaseModel):
    systemPrompt: Optional[str] = None
    messages: List[ChatMessage] = []
    userMessage: str
    images: Optional[List[str]] = None  # base64 data URLs for current turn
    userId: Optional[str] = None  # 用户ID，用于记忆查询
    companionId: Optional[str] = None  # 伴侣ID，用于 RAG 知识库路由


class SuggestionsRequest(BaseModel):
    systemPrompt: Optional[str] = None
    messages: List[ChatMessage] = []


class AvatarRequest(BaseModel):
    personality: str
    description: str


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str


# ── Cache helpers ──────────────────────────────────────────────────────────────

def _cache_set(key: str, value: str, ttl: int = _cache_ttl):
    if _redis_available:
        try:
            _redis.setex(key, ttl, value)
            return
        except Exception:
            pass
    _response_cache[key] = {"value": value, "expires": time.time() + ttl}

def _cache_get(key: str) -> Optional[str]:
    if _redis_available:
        try:
            return _redis.get(key)
        except Exception:
            pass
    entry = _response_cache.get(key)
    if entry and time.time() < entry["expires"]:
        return entry["value"]
    return None

def _session_set(session_id: str, messages: List[Dict], ttl: int = 86400):
    payload = json.dumps(messages, ensure_ascii=False)
    if _redis_available:
        try:
            _redis.setex(f"session:{session_id}", ttl, payload)
            return
        except Exception:
            pass
    _session_cache[session_id] = {"messages": messages, "expires": time.time() + ttl}

def _session_get(session_id: str) -> List[Dict]:
    if _redis_available:
        try:
            raw = _redis.get(f"session:{session_id}")
            return json.loads(raw) if raw else []
        except Exception:
            pass
    entry = _session_cache.get(session_id)
    if entry and time.time() < entry["expires"]:
        return entry["messages"]
    return []


def _extract_personality(system_prompt: Optional[str]) -> str:
    personality = "温柔体贴"
    if system_prompt:
        for key in PRESET_RESPONSES.keys():
            if key in system_prompt:
                personality = key
                break
    return personality


def _normalize_role(role: str) -> Optional[str]:
    r = (role or "").strip().lower()
    if r in ("assistant", "ai", "bot"):
        return "assistant"
    if r in ("user", "human"):
        return "user"
    if r == "system":
        return "system"
    return None


def _build_messages(
    user_message: str,
    system_prompt: Optional[str],
    history_messages: Optional[List[ChatMessage]],
    personality: str,
    images: Optional[List[str]] = None,
) -> List[Dict]:
    """Build the messages list with an optimised system prompt. Supports multimodal content."""
    base_prompt = system_prompt or (
        f"你是一个{personality}的AI伴侣。请遵守以下原则：\n"
        "1. 用自然、真诚、有温度的语言回复，避免机械感。\n"
        "2. 回复长度控制在100-250字，简洁而有内容。\n"
        "3. 根据对话上下文保持话题连贯性。\n"
        "4. 情感表达要细腻真实，体现对用户的关心。\n"
        "5. 不重复使用相同的开场白或句式。"
    )
    messages: List[Dict] = [{"role": "system", "content": base_prompt}]

    # 历史消息里的图片无法回传（落库的是本机 uploads URL，云端模型访问不到），
    # 用一条 system 说明一次性告知，而不是往每条历史 content 里塞占位文字——
    # 后者会被模型理解成"用户说过图片没传过来"，进而忽略当前轮真正附带的图片。
    history_image_dropped = any(
        getattr(m, "images", None) for m in (history_messages or [])
        if any(isinstance(i, str) and not i.startswith("data:") for i in getattr(m, "images", None) or [])
    )
    if history_image_dropped:
        messages.append({
            "role": "system",
            "content": "（说明：更早的对话中用户发过图片，但历史图片未随上下文传输，"
                       "你只需回应本轮内容，不要声称用户没有发图。）",
        })

    if history_messages:
        for m in history_messages[-12:]:
            role = _normalize_role(getattr(m, "role", None))
            if role in ("user", "assistant"):
                content = (getattr(m, "content", "") or "").strip()
                if not content:
                    continue
                msg_images = getattr(m, "images", None)
                # 历史图片只保留 data URL（base64）。落库的 http://localhost/uploads/*
                # 是开发机地址，云端模型访问不到，传过去会让整条请求 400
                # 「图片输入格式/解析错误」，进而整条链降级成预设文案。
                history_data_images = [
                    img for img in (msg_images or [])
                    if isinstance(img, str) and img.startswith("data:")
                ]
                if history_data_images:
                    parts: List[Dict] = [{"type": "text", "text": content}]
                    for img_url in history_data_images:
                        parts.append({"type": "image_url", "image_url": {"url": img_url}})
                    messages.append({"role": role, "content": parts})
                else:
                    # 历史图片无法回传时不做任何拼接：把占位文字混进 content 会让模型
                    # 以为"用户说过图片没传过来"，从而忽略当前这轮真正附带的图片。
                    messages.append({"role": role, "content": content})

    # Build current user turn（只接受 data URL：云端模型无法访问 localhost 落盘地址）
    data_images = [img for img in (images or []) if isinstance(img, str) and img.startswith("data:")]
    if data_images:
        parts = [{"type": "text", "text": user_message or "请描述这张图片的内容。"}]
        for img_url in data_images:
            parts.append({"type": "image_url", "image_url": {"url": img_url}})
        user_turn: Dict = {"role": "user", "content": parts}
    else:
        # 有图片但都不是 data URL（例如误传了 localhost 落盘地址）时，
        # 明确告知模型图片未能附带，避免它凭空编造图片内容。
        text = user_message
        if images and not text:
            text = "（图片未能传输给模型，请让用户用文字描述）"
        user_turn = {"role": "user", "content": text}

    last = messages[-1] if messages else None
    if not last or last.get("role") != "user":
        messages.append(user_turn)

    return messages


def generate_smart_response(
    user_message: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[List[ChatMessage]] = None,
    session_id: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> str:
    personality = _extract_personality(system_prompt)

    # Skip cache when images or history context present
    if not history_messages and not images:
        cache_key = f"resp:{hashlib.md5(f'{personality}:{user_message}'.encode()).hexdigest()}"
        cached = _cache_get(cache_key)
        if cached:
            return cached

    client, model, effective_images = _route_llm(images)
    if client:
        try:
            messages = _build_messages(user_message, system_prompt, history_messages, personality, effective_images)

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.72,
                max_completion_tokens=512,
                top_p=0.9,
                extra_body={"thinking": {"type": "disabled"}},
            )

            content = response.choices[0].message.content
            if content and str(content).strip():
                result = str(content).strip()
                if not history_messages and not images:
                    _cache_set(cache_key, result)
                return result
        except Exception as e:
            print(f"Zhipu AI error: {e}")

    responses = PRESET_RESPONSES.get(personality, PRESET_RESPONSES["温柔体贴"])
    return random.choice(responses)


async def stream_smart_response(
    user_message: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[List[ChatMessage]] = None,
    images: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted chunks. Falls back to simulated streaming if API unavailable."""
    personality = _extract_personality(system_prompt)

    client, model, effective_images = _route_llm(images)
    if client:
        try:
            messages = _build_messages(user_message, system_prompt, history_messages, personality, effective_images)

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.72,
                max_completion_tokens=512,
                top_p=0.9,
                stream=True,
                extra_body={"thinking": {"type": "disabled"}},
            )

            for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    data = json.dumps({"delta": delta, "done": False}, ensure_ascii=False)
                    yield f"data: {data}\n\n"

            yield f"data: {json.dumps({'delta': '', 'done': True})}\n\n"
            return
        except Exception as e:
            print(f"Zhipu AI stream error: {e}")

    # Fallback: simulate streaming from preset response
    fallback = random.choice(PRESET_RESPONSES.get(personality, PRESET_RESPONSES["温柔体贴"]))
    for char in fallback:
        data = json.dumps({"delta": char, "done": False}, ensure_ascii=False)
        yield f"data: {data}\n\n"
        await asyncio.sleep(0.02)
    yield f"data: {json.dumps({'delta': '', 'done': True})}\n\n"


def _svg_avatar_data_url(seed: str, label: str) -> str:
    s = (seed or "default").encode("utf-8")
    h = hashlib.sha256(s).hexdigest()
    c1 = f"#{h[0:6]}"
    c2 = f"#{h[6:12]}"
    text = (label or "AI").strip()[:2]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="64" fill="url(#g)"/>
  <text x="50%" y="54%" text-anchor="middle" dominant-baseline="middle"
        font-family="system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial"
        font-size="88" fill="rgba(255,255,255,0.92)" font-weight="700">{text}</text>
</svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


@app.get("/health", tags=["Health"])
async def health_check():
    return APIResponse(
        success=True,
        message="Service is healthy",
        data={
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "llm_available": llm_client is not None,
            "vision_available": vision_client is not None,
            "model": ZHIPU_MODEL,
            "vision_model": ZHIPU_VISION_MODEL,
            "image_model": ZHIPU_IMAGE_MODEL or None
        },
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/", tags=["Root"])
async def root():
    return APIResponse(
        success=True,
        message="Welcome to AI Companion AI Service",
        data={"version": "1.0.0", "name": "AI Companion AI Service"},
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/api/v1/ai/chat", tags=["AI"])
async def chat(request: ChatRequest):
    try:
        with tracer.measure("chat"):
            ai_response = generate_smart_response(
                request.userMessage,
                request.systemPrompt,
                request.messages,
                images=request.images,
            )
        return APIResponse(
            success=True,
            message="Chat generated successfully",
            data={"content": ai_response},
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ai/chat/stream", tags=["AI"], dependencies=[Depends(verify_service_token)])
async def chat_stream(request: ChatRequest):
    """SSE streaming endpoint – sends tokens as they arrive from the model."""
    return StreamingResponse(
        stream_smart_response(
            request.userMessage,
            request.systemPrompt,
            request.messages,
            images=request.images,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/v1/ai/suggestions", tags=["AI"])
async def get_suggestions(request: SuggestionsRequest):
    """Generate context-aware quick-reply suggestions based on conversation history."""
    personality = _extract_personality(request.systemPrompt)
    default_suggestions = ["你好呀 👋", "今天过得怎么样？", "给我讲个笑话 😄", "陪我聊聊天"]

    if not llm_client or not request.messages:
        return APIResponse(
            success=True,
            message="Suggestions generated",
            data={"suggestions": default_suggestions},
            timestamp=datetime.utcnow().isoformat(),
        )

    try:
        history_snippet = []
        for m in request.messages[-6:]:
            role = _normalize_role(getattr(m, "role", None))
            if role in ("user", "assistant"):
                content = (getattr(m, "content", "") or "").strip()
                if content:
                    history_snippet.append(f"{'用户' if role == 'user' else 'AI'}: {content}")

        prompt_text = (
            "根据以下对话记录，生成4条简短的用户可能想说的下一句话（建议话术）。"
            "要求：符合当前对话情绪和话题，每条不超过15字，输出格式为JSON数组，如 [\"话语1\",\"话语2\",\"话语3\",\"话语4\"]，不要加任何其他内容。\n\n"
            "对话记录：\n" + "\n".join(history_snippet)
        )

        response = llm_client.chat.completions.create(
            model=ZHIPU_MODEL,
            messages=[
                {"role": "system", "content": f"你是一个{personality}的AI伴侣对话助手。"},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.8,
            max_completion_tokens=200,
            extra_body={"thinking": {"type": "disabled"}},
        )

        raw = (response.choices[0].message.content or "").strip()
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            suggestions = json.loads(raw[start:end + 1])
            if isinstance(suggestions, list) and suggestions:
                return APIResponse(
                    success=True,
                    message="Suggestions generated",
                    data={"suggestions": suggestions[:4]},
                    timestamp=datetime.utcnow().isoformat(),
                )
    except Exception as e:
        print(f"Suggestions error: {e}")

    return APIResponse(
        success=True,
        message="Suggestions generated",
        data={"suggestions": default_suggestions},
        timestamp=datetime.utcnow().isoformat(),
    )


@app.get("/api/v1/metrics", tags=["Metrics"])
async def get_metrics():
    raw = tracer.get_metrics()
    summary = {}
    for op, entries in raw.items():
        if entries:
            durations = [e["duration"] for e in entries]
            summary[op] = {
                "count": len(durations),
                "avg_ms": round(sum(durations) / len(durations) * 1000, 1),
                "min_ms": round(min(durations) * 1000, 1),
                "max_ms": round(max(durations) * 1000, 1),
                "p95_ms": round(sorted(durations)[int(len(durations) * 0.95)] * 1000, 1),
            }
    return APIResponse(
        success=True,
        message="Metrics retrieved",
        data={"operations": summary, "redis_available": _redis_available},
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post("/api/v1/ai/generate-avatar", tags=["AI"])
async def generate_avatar(request: AvatarRequest):
    """生成 AI 头像。

    降级路径必须可观测：返回的 message 明确区分「AI 成功」与「本地 SVG 降级」，
    并在 data.fallback 里给出布尔值与原因，供前端提示用户——
    历史上静默降级曾让"图像模型没生效"被误判为前端问题。
    """
    try:
        fallback_reason = ""

        # 仅当配置了远程图像模型（ZHIPU_IMAGE_MODEL 非空）才调用；置空直接走本地 SVG 降级
        if not ZHIPU_IMAGE_MODEL:
            fallback_reason = "未配置 ZHIPU_IMAGE_MODEL"
            print(f"[avatar] {fallback_reason}，使用本地 SVG 头像")
        elif not llm_client:
            fallback_reason = "LLM 客户端未初始化（ZHIPU_API_KEY 为空？）"
            print(f"[avatar] {fallback_reason}，使用本地 SVG 头像")
        else:
            try:
                prompt = f"可爱的动漫风格头像，{request.personality}，{request.description}，高清，高质量"
                # 智谱图像生成走 /images/generations（OpenAI 兼容），
                # openai SDK 3.x 的方法名是 images.generate
                response = llm_client.images.generate(
                    model=ZHIPU_IMAGE_MODEL,
                    prompt=prompt,
                    size="1024x1024"
                )
                avatar_url = response.data[0].url
                print(f"[avatar] Generated using remote image model: {ZHIPU_IMAGE_MODEL}")

                return APIResponse(
                    success=True,
                    message="Avatar generated successfully using AI",
                    data={
                        "avatarUrl": avatar_url,
                        "fallback": False,
                        "model": ZHIPU_IMAGE_MODEL,
                    },
                    timestamp=datetime.utcnow().isoformat()
                )
            except Exception as e:
                fallback_reason = f"{type(e).__name__}: {e}"
                print(f"[avatar] Remote image generation failed ({fallback_reason})，使用本地 SVG 头像")

        seed = f"{request.personality}-{request.description}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        label = (request.personality or "AI").strip()[:2]
        avatar_url = _svg_avatar_data_url(seed, label)

        return APIResponse(
            success=True,
            message=f"Avatar fallback (SVG), 原因: {fallback_reason}",
            data={
                "avatarUrl": avatar_url,
                "fallback": True,
                "fallbackReason": fallback_reason,
            },
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        print(f"Error in generate-avatar endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── LangChain 增强接口 ──────────────────────────────────────────────

@app.post("/api/v1/ai/chat/langchain", tags=["AI", "LangChain"])
async def chat_langchain(request: ChatRequest):
    """使用 LangChain + Function Calling 增强的聊天接口"""
    try:
        with tracer.measure("chat_langchain"):
            personality = _extract_personality(request.systemPrompt)

            # 带图请求绕过 LangChain Agent（同流式接口的原因：Agent 无法承载 image_url）
            if request.images:
                ai_response = generate_smart_response(
                    request.userMessage,
                    request.systemPrompt,
                    request.messages,
                    images=request.images,
                )
                return APIResponse(
                    success=True,
                    message="Chat generated successfully (Vision)",
                    data={"content": ai_response, "engine": "vision"},
                    timestamp=datetime.utcnow().isoformat(),
                )

            # 格式化历史消息
            history = []
            for m in request.messages:
                role = _normalize_role(m.role)
                if role:
                    history.append({
                        "role": role,
                        "content": m.content
                    })

            # 优先使用 LangChain
            if langchain_client:
                try:
                    result = langchain_client.chat(
                        user_input=request.userMessage,
                        chat_history=history,
                        personality=personality,
                        user_id=request.userId,
                        system_prompt=request.systemPrompt,
                    )
                    return APIResponse(
                        success=True,
                        message="Chat generated successfully (LangChain)",
                        data={"content": result["content"], "engine": "langchain"},
                        timestamp=datetime.utcnow().isoformat(),
                    )
                except Exception as e:
                    print(f"LangChain error: {e}, falling back to original")
            
            # 降级到原始方法
            ai_response = generate_smart_response(
                request.userMessage,
                request.systemPrompt,
                request.messages,
                images=request.images,
            )
            return APIResponse(
                success=True,
                message="Chat generated successfully (Fallback)",
                data={"content": ai_response, "engine": "fallback"},
                timestamp=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ai/chat/langchain/stream", tags=["AI", "LangChain"], dependencies=[Depends(verify_service_token)])
async def chat_langchain_stream(request: ChatRequest):
    """LangChain 流式接口 - 支持 Function Calling 的流式聊天"""

    async def generate():
        try:
            personality = _extract_personality(request.systemPrompt)

            # 带图请求绕过 LangChain Agent：Agent 的 HumanMessage 只承载纯文本，
            # 无法传 image_url，图片会被静默丢弃（AI 会答"我没收到图片"）。
            # 视觉理解用不上 Function Calling，直接走 stream_smart_response 的视觉路由。
            # 代价：该条消息不触发记忆/知识库检索。
            if request.images:
                async for sse_chunk in stream_smart_response(
                    request.userMessage,
                    request.systemPrompt,
                    request.messages,
                    request.images
                ):
                    yield sse_chunk
                return

            # 格式化历史消息
            history = []
            for m in request.messages:
                role = _normalize_role(m.role)
                if role:
                    history.append({
                        "role": role,
                        "content": m.content
                    })

            if langchain_client:
                try:
                    async for chunk in langchain_client.chat_stream(
                        user_input=request.userMessage,
                        chat_history=history,
                        personality=personality,
                        user_id=request.userId,
                        companion_id=request.companionId,
                        system_prompt=request.systemPrompt,
                    ):
                        data = json.dumps({"delta": chunk, "done": False}, ensure_ascii=False)
                        yield f"data: {data}\n\n"

                    yield f"data: {json.dumps({'delta': '', 'done': True})}\n\n"
                    return
                except Exception as e:
                    print(f"LangChain stream error: {e}, falling back")

            # 降级到原始流式方法
            async for sse_chunk in stream_smart_response(
                request.userMessage,
                request.systemPrompt,
                request.messages,
                request.images
            ):
                yield sse_chunk
        
        except Exception as e:
            print(f"Stream error: {e}")
            # 终极降级
            fallback = random.choice(PRESET_RESPONSES.get(personality, PRESET_RESPONSES["温柔体贴"]))
            for char in fallback:
                data = json.dumps({"delta": char, "done": False}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.02)
            yield f"data: {json.dumps({'delta': '', 'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── 记忆与心情管理接口 ──────────────────────────────────────────────

class MemoryCreateRequest(BaseModel):
    userId: str
    memoryType: str = "fact"
    keyword: Optional[str] = None
    content: str


class MoodCreateRequest(BaseModel):
    userId: str
    mood: str
    score: float = 5.0
    note: Optional[str] = None


class MemoryUpdateRequest(BaseModel):
    """记忆更新请求。userId 必填用于归属校验；其余字段为 None 表示不修改。"""
    userId: str
    memoryType: Optional[str] = None
    keyword: Optional[str] = None
    content: Optional[str] = None


@app.get("/api/v1/memory/{user_id}", tags=["Memory"])
async def get_user_memory(user_id: str, keyword: Optional[str] = None):
    """查询用户记忆"""
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MemoryService

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="数据库未配置或连接失败")

        with SessionLocal() as db:
            service = MemoryService(db)
            memories = service.search_user_memory(user_id, keyword or "")
            return APIResponse(
                success=True,
                message="Memory retrieved",
                data={
                    "memories": [
                        {
                            "id": m.id,
                            "userId": m.user_id,
                            "type": m.memory_type,
                            "keyword": m.keyword,
                            "content": m.content,
                            "createdAt": m.created_at.isoformat() if m.created_at else None,
                        }
                        for m in memories
                    ]
                },
                timestamp=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/memory", tags=["Memory"])
async def create_memory(request: MemoryCreateRequest):
    """添加用户记忆"""
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MemoryService

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="数据库未配置或连接失败")

        with SessionLocal() as db:
            service = MemoryService(db)
            keyword = request.keyword or (request.content[:20] if len(request.content) <= 20 else request.content[:20] + "...")
            memory = service.add_user_memory(
                user_id=request.userId,
                memory_type=request.memoryType,
                keyword=keyword,
                content=request.content,
            )
            # 双写向量：与 LangChain 的 add_user_memory 工具保持同一口径。
            # 历史版本这里只写 SQLite，导致编辑/删除时的向量同步全是空转。
            _sync_memory_vector_on_create(request.userId, memory.id, request.content, request.memoryType)
            return APIResponse(
                success=True,
                message="Memory added",
                data={
                    "id": memory.id,
                    "userId": memory.user_id,
                    "type": memory.memory_type,
                    "keyword": memory.keyword,
                    "content": memory.content,
                    "createdAt": memory.created_at.isoformat() if memory.created_at else None,
                },
                timestamp=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _sync_memory_vector_on_create(user_id: str, memory_id: int, content: str, memory_type: str = "fact") -> None:
    """新建记忆后写入向量。与新增的 SQLite 行同事务语义不同——Chroma 失败只 warning。

    写入 metadata 里带 memory_id，后续编辑/删除可按 id 精确清理。
    """
    try:
        from app.ai.rag import get_rag_store
        store = get_rag_store()
        if store is None:
            return
        store.add_memory(user_id=user_id, content=content, memory_type=memory_type, memory_id=memory_id)
    except Exception as e:
        print(f"[memory] 向量写入失败（不影响数据库结果）: {e}")


def _sync_memory_vector_on_update(
    user_id: str, memory_id: int, old_content: str, new_content: str, memory_type: str = "fact"
) -> None:
    """记忆内容变更后同步向量：删旧 + 写新（自愈：旧向量不存在也照写新向量）。

    Chroma 是检索加速层，事实源是 SQLite。这里任何异常都只记 warning 不外抛——
    「SQLite 成功、Chroma 失败」不会让功能出错，因为 search_user_memory 走的是 SQL ilike。
    写入一定要在删除之后无条件执行：历史数据可能压根没有向量（POST 端点曾漏写），
    若因「没删到旧向量」就跳过写入，向量层会永久缺失这条记忆。
    """
    try:
        from app.ai.rag import get_rag_store
        store = get_rag_store()
        if store is None:
            return
        store.delete_memory(user_id=user_id, memory_id=memory_id, content=old_content)
        store.add_memory(
            user_id=user_id, content=new_content, memory_type=memory_type, memory_id=memory_id
        )
    except Exception as e:
        print(f"[memory] 向量同步失败（不影响数据库结果）: {e}")


def _sync_memory_vector_on_delete(user_id: str, memory_id: int, content: str) -> None:
    """记忆删除后清理向量。失败仅 warning，同上。"""
    try:
        from app.ai.rag import get_rag_store
        store = get_rag_store()
        if store is None:
            return
        store.delete_memory(user_id=user_id, memory_id=memory_id, content=content)
    except Exception as e:
        print(f"[memory] 向量清理失败（不影响数据库结果）: {e}")


@app.put("/api/v1/memory/{memory_id}", tags=["Memory"])
async def update_memory(memory_id: int, request: MemoryUpdateRequest):
    """编辑记忆。

    归属校验：userId 必须与记忆的 user_id 一致，否则按 404 处理（不区分「不存在」与「无权」，
    避免通过状态码探测他人记忆是否存在）。
    """
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MemoryService

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="数据库未配置或连接失败")

        with SessionLocal() as db:
            service = MemoryService(db)
            old = service.get_memory_by_id(memory_id)
            if old is None or old.user_id != request.userId:
                raise HTTPException(status_code=404, detail="记忆不存在")

            old_content = old.content
            memory = service.update_user_memory(
                memory_id=memory_id,
                user_id=request.userId,
                memory_type=request.memoryType,
                keyword=request.keyword,
                content=request.content,
            )
            if memory is None:
                raise HTTPException(status_code=404, detail="记忆不存在")

            # 只有内容真变了才动向量；改分类不用重建
            content_changed = old_content != memory.content
            if content_changed:
                _sync_memory_vector_on_update(
                    request.userId, memory_id, old_content, memory.content, memory.memory_type
                )

            return APIResponse(
                success=True,
                message="Memory updated",
                data={
                    "id": memory.id,
                    "userId": memory.user_id,
                    "type": memory.memory_type,
                    "keyword": memory.keyword,
                    "content": memory.content,
                    "createdAt": memory.created_at.isoformat() if memory.created_at else None,
                },
                timestamp=datetime.utcnow().isoformat(),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/memory/{memory_id}", tags=["Memory"])
async def delete_memory(memory_id: int, userId: str):
    """删除记忆。userId 走 query 参数（DELETE 不带 body 更符合规范）。"""
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MemoryService

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="数据库未配置或连接失败")

        with SessionLocal() as db:
            service = MemoryService(db)
            old = service.get_memory_by_id(memory_id)
            if old is None or old.user_id != userId:
                raise HTTPException(status_code=404, detail="记忆不存在")

            old_content = old.content
            deleted = service.delete_user_memory(memory_id=memory_id, user_id=userId)
            if not deleted:
                raise HTTPException(status_code=404, detail="记忆不存在")

            _sync_memory_vector_on_delete(userId, memory_id, old_content)

            return APIResponse(
                success=True,
                message="Memory deleted",
                data={"id": memory_id},
                timestamp=datetime.utcnow().isoformat(),
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/mood/{user_id}", tags=["Mood"])
async def get_user_mood(user_id: str, days: int = 7):
    """查询用户心情历史"""
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MoodService

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="数据库未配置或连接失败")

        with SessionLocal() as db:
            service = MoodService(db)
            moods = service.get_mood_history(user_id, days)
            return APIResponse(
                success=True,
                message="Mood history retrieved",
                data={
                    "moods": [
                        {
                            "id": m.id,
                            "userId": m.user_id,
                            "mood": m.mood,
                            "score": m.score,
                            "note": m.note,
                            "createdAt": m.created_at.isoformat() if m.created_at else None,
                        }
                        for m in moods
                    ]
                },
                timestamp=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/mood", tags=["Mood"])
async def create_mood(request: MoodCreateRequest):
    """记录用户心情"""
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MoodService

        if SessionLocal is None:
            raise HTTPException(status_code=503, detail="数据库未配置或连接失败")

        with SessionLocal() as db:
            service = MoodService(db)
            mood = service.add_user_mood(
                user_id=request.userId,
                mood=request.mood,
                score=request.score,
                note=request.note,
            )
            return APIResponse(
                success=True,
                message="Mood recorded",
                data={
                    "id": mood.id,
                    "userId": mood.user_id,
                    "mood": mood.mood,
                    "score": mood.score,
                    "note": mood.note,
                    "createdAt": mood.created_at.isoformat() if mood.created_at else None,
                },
                timestamp=datetime.utcnow().isoformat(),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 5000))
    debug = os.getenv("APP_DEBUG", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
