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
from fastapi import FastAPI, HTTPException, Request
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

# Initialize Zhipu AI client (with fallback)
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4.5-air")
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")
ZHIPU_IMAGE_MODEL = os.getenv("ZHIPU_IMAGE_MODEL", "cogview-3")

zhipu_client = None
try:
    from zhipuai import ZhipuAI
    if ZHIPU_API_KEY:
        try:
            zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
            print(f"Successfully initialized Zhipu AI client with model: {ZHIPU_MODEL}, image model: {ZHIPU_IMAGE_MODEL}")
        except Exception as e:
            print(f"Failed to initialize Zhipu AI client: {e}")
except ImportError:
    print("ZhipuAI SDK not installed, will use fallback responses")


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

    if history_messages:
        for m in history_messages[-12:]:
            role = _normalize_role(getattr(m, "role", None))
            if role in ("user", "assistant"):
                content = (getattr(m, "content", "") or "").strip()
                if not content:
                    continue
                msg_images = getattr(m, "images", None)
                if msg_images:
                    parts: List[Dict] = [{"type": "text", "text": content}]
                    for img_url in msg_images:
                        parts.append({"type": "image_url", "image_url": {"url": img_url}})
                    messages.append({"role": role, "content": parts})
                else:
                    messages.append({"role": role, "content": content})

    # Build current user turn
    if images:
        parts = [{"type": "text", "text": user_message or "请描述这张图片的内容。"}]
        for img_url in images:
            parts.append({"type": "image_url", "image_url": {"url": img_url}})
        user_turn: Dict = {"role": "user", "content": parts}
    else:
        user_turn = {"role": "user", "content": user_message}

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

    if zhipu_client:
        try:
            model = ZHIPU_VISION_MODEL if images else ZHIPU_MODEL
            messages = _build_messages(user_message, system_prompt, history_messages, personality, images)

            response = zhipu_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.72,
                max_tokens=512,
                top_p=0.9,
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

    if zhipu_client:
        try:
            model = ZHIPU_VISION_MODEL if images else ZHIPU_MODEL
            messages = _build_messages(user_message, system_prompt, history_messages, personality, images)

            response = zhipu_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.72,
                max_tokens=512,
                top_p=0.9,
                stream=True,
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
            "zhipu_available": zhipu_client is not None,
            "model": ZHIPU_MODEL,
            "image_model": ZHIPU_IMAGE_MODEL
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


@app.post("/api/v1/ai/chat/stream", tags=["AI"])
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

    if not zhipu_client or not request.messages:
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

        response = zhipu_client.chat.completions.create(
            model=ZHIPU_MODEL,
            messages=[
                {"role": "system", "content": f"你是一个{personality}的AI伴侣对话助手。"},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.8,
            max_tokens=200,
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
    try:
        # Try using Zhipu AI image model first
        if zhipu_client:
            try:
                # Generate avatar using CogView 3
                prompt = f"可爱的动漫风格头像，{request.personality}，{request.description}，高清，高质量"
                response = zhipu_client.images.generations.create(
                    model=ZHIPU_IMAGE_MODEL,
                    prompt=prompt,
                    size="1024x1024"
                )
                avatar_url = response.data[0].url
                print(f"Generated avatar using Zhipu AI image model")
                
                return APIResponse(
                    success=True,
                    message="Avatar generated successfully using AI",
                    data={
                        "avatarUrl": avatar_url
                    },
                    timestamp=datetime.utcnow().isoformat()
                )
            except Exception as e:
                print(f"Zhipu AI image generation error: {e}, falling back to local avatar")

        seed = f"{request.personality}-{request.description}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        label = (request.personality or "AI").strip()[:2]
        avatar_url = _svg_avatar_data_url(seed, label)
        
        return APIResponse(
            success=True,
            message="Avatar generated successfully",
            data={
                "avatarUrl": avatar_url
            },
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        print(f"Error in generate-avatar endpoint: {e}")
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
