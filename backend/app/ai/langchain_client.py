"""
LangChain 客户端 —— 智谱 GLM（glm-4.5-air）Function Calling + RAG。

工作方式：
1. chat() 把 prompt | self.llm、tools 交给 LangChain，由 LLM 决定是否调用工具。
   例如用户问"我生日是什么时候" -> 调用 search_user_memory -> 拿到结果 -> 回答。
2. 使用 LangChain 1.x 的 create_agent() 构建 Agent，工具调用循环全自动。
3. 挂载 RAG 工具 search_knowledge，支持知识库检索增强。
4. chat() / chat_stream() 均带完整异常兜底，失败由上层降级。

说明：本链路保留模型思考（thinking），换取工具选择与多步推理质量；
低延迟的普通对话走 main.py 直连链路（thinking 关闭）。
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

# LangChain 1.x 中 AgentExecutor / create_tool_calling_agent 已由 create_agent 取代
from langchain.agents import create_agent

# 联网搜索工具（可选依赖，缺失时自动跳过）
try:
    from langchain_community.tools import DuckDuckGoSearchRun
    _WEB_SEARCH_AVAILABLE = True
except Exception:
    DuckDuckGoSearchRun = None
    _WEB_SEARCH_AVAILABLE = False

from app.ai.prompts import build_system_prompt

logger = logging.getLogger(__name__)


def _search_knowledge_remote(companion_id: str, query: str, config) -> Optional[str]:
    """调 8002 RAG 服务检索知识库。

    Returns:
        - 有 chunks：拼接后的检索文本（不回落）
        - 空 chunks：提示语（正常业务结果，不回落）
        - 4xx：None，调用方收到 None 后走本地兜底
    Raises:
        超时 / 连接异常 / HTTP 5xx 时抛异常，由调用方回落本地。
    """
    import requests

    resp = requests.post(
        config.RAG_SERVICE_URL + "/api/v1/kb/retrieve",
        json={"companionId": companion_id, "query": query, "topK": 4},
        timeout=config.RAG_TIMEOUT,
    )
    # 5xx 视为故障，抛异常触发回落
    if resp.status_code >= 500:
        raise RuntimeError("RAG 8002 返回 " + str(resp.status_code))
    # 4xx 多为请求参数问题（如 companionId 未绑定知识库），记一条 warning 后返回 None；
    # 调用方收到 None 会走本地兜底（行为与 5xx 一致，但不再抛出异常打断 Agent 链路）
    if resp.status_code >= 400:
        logger.warning("[search_knowledge] 8002 返回 %d: %s", resp.status_code, resp.text[:200])
        return None

    data = resp.json().get("data", {})
    chunks = data.get("chunks", [])
    if not chunks:
        return "知识库中没有找到相关内容。"
    return "\n".join(c["content"].strip() for c in chunks if c.get("content", "").strip())


class NaturalLanguageOutputParser:
    """把 Agent 输出转成自然语言（去 Markdown 痕迹）"""

    @staticmethod
    def parse(text: str) -> str:
        """清理 Markdown 语法，保留纯文本"""
        if not text:
            return ""
        text = text.replace("```", "").replace("``", "")

        import re
        text = re.sub(r"<[^>]+>", "", text)

        lines = text.split("\n")
        processed_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                processed_lines.append("")
                continue
            if line.startswith("#"):
                line = line.replace("#", "").strip()
            while line.startswith(("*", "?", "-", "+")):
                line = line[1:].strip()
            line = line.replace("**", "").replace("*", "").replace("_", "")
            if line:
                processed_lines.append(line)

        result = []
        for line in processed_lines:
            if line.strip() == "":
                if result and result[-1].strip() != "":
                    result.append("")
            else:
                result.append(line)

        return "\n".join(result).strip()


def create_llm():
    """创建文本链路 LLM（智谱 GLM，OpenAI 兼容协议）"""
    from app.ai.config import LLMConfig
    config = LLMConfig()

    if not config.is_valid():
        raise ValueError("LLM API 配置无效：ZHIPU_API_KEY 为空")

    return ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
        top_p=config.TOP_P,
    )


class LangChainGLMClient:
    """LangChain Agent 客户端（Function Calling + RAG）"""

    def __init__(self):
        from app.ai.config import LLMConfig
        self.config = LLMConfig()

        self.llm = create_llm()
        # 无 companionId 的默认工具集 + agent（单例，供无 companionId 场景复用）
        self.tools = self._init_tools()
        self.agent = self._build_agent(self.tools)
        print("[LangChain] Agent ready, tools: " + str([t.name for t in self.tools]))

    def _build_agent(self, tools: List[Any]):
        """用指定工具集构建 Agent（每次调用都是纯内存操作，开销 <1ms）"""
        return create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=build_system_prompt(),
        )

    def _init_tools(self, companion_id: Optional[str] = None) -> List[Any]:
        """初始化全部工具（Function Calling）。

        Args:
            companion_id: 伴侣 ID，传入时 search_knowledge 闭包会优先调 8002 RAG 服务。
        """
        tools: List[Any] = []

        if _WEB_SEARCH_AVAILABLE:
            try:
                tools.append(
                    DuckDuckGoSearchRun(
                        name="web_search",
                        description="联网搜索工具。用户询问实时信息（新闻、天气、股价、日期相关）时使用。",
                    )
                )
            except Exception as e:
                print("[LangChain] web_search init failed: " + str(e))

        @tool
        def search_user_memory(user_id: str, keyword: str) -> str:
            """查询关于某个用户的记忆（数据库 + RAG 知识库双路检索）。

            当用户询问"我之前说过什么""我的偏好/生日/习惯"等与用户个人历史相关的问题时使用。

            Args:
                user_id: 用户ID
                keyword: 检索关键词

            Returns:
                多条记忆内容拼接；无记忆时返回提示语
            """
            results: List[str] = []

            try:
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                if SessionLocal is not None:
                    with SessionLocal() as db:
                        memories = MemoryService(db).search_user_memory(user_id, keyword)
                        for m in memories or []:
                            results.append(str(m.keyword) + "：" + str(m.content))
            except Exception as e:
                print("[search_user_memory] db failed: " + str(e))

            try:
                from app.ai.rag import get_rag_store
                store = get_rag_store()
                if store is not None:
                    docs = store.search(keyword, user_id=user_id, k=3)
                    for d in docs:
                        text = d.page_content.strip()
                        if text and text not in results:
                            results.append(text)
            except Exception as e:
                print("[search_user_memory] rag failed: " + str(e))

            if not results:
                return "没有找到与" + keyword + "相关的记忆。"
            return "；".join(results)

        tools.append(search_user_memory)

        @tool
        def get_mood_history(user_id: str, days: int = 7) -> str:
            """查询用户最近的心情历史。

            当用户询问"我最近心情怎么样""记录一下我的心情"等情绪相关话题时使用。

            Args:
                user_id: 用户ID
                days: 查询最近多少天，默认7天

            Returns:
                心情记录列表；无记录时返回提示语
            """
            try:
                from app.database import SessionLocal
                from app.services.memory_service import MoodService

                if SessionLocal is None:
                    return "心情数据暂不可用（数据库未配置）。"

                with SessionLocal() as db:
                    moods = MoodService(db).get_mood_history(user_id, days)
                    if not moods:
                        return "最近" + str(days) + "天没有心情记录。"
                    parts = []
                    for m in moods:
                        s = str(m.mood) + "（" + str(m.score) + "分）"
                        if m.note:
                            s += "：" + str(m.note)
                        parts.append(s)
                    return "；".join(parts)
            except Exception as e:
                print("[get_mood_history] failed: " + str(e))
                return "心情记录查询失败。"

        tools.append(get_mood_history)

        @tool
        def add_user_memory(user_id: str, memory_type: str, content: str) -> str:
            """保存一条关于用户的记忆（双写：数据库 + RAG 知识库）。

            当用户陈述值得长期记住的信息（生日、喜好、习惯、重要事件）时使用。

            Args:
                user_id: 用户ID
                memory_type: 记忆类型，如 fact / preference / birthday 等
                content: 记忆内容

            Returns:
                保存结果反馈
            """
            keyword = content[:20]
            ok_db = False
            ok_rag = False

            try:
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                if SessionLocal is not None:
                    with SessionLocal() as db:
                        MemoryService(db).add_user_memory(
                            user_id=user_id,
                            memory_type=memory_type,
                            keyword=keyword,
                            content=content,
                        )
                        ok_db = True
            except Exception as e:
                print("[add_user_memory] db failed: " + str(e))

            try:
                from app.ai.rag import get_rag_store
                store = get_rag_store()
                if store is not None:
                    store.add_memory(user_id=user_id, content=content, memory_type=memory_type)
                    ok_rag = True
            except Exception as e:
                print("[add_user_memory] rag failed: " + str(e))

            if ok_db or ok_rag:
                return "记忆已保存：" + content
            return "记忆保存失败（数据库与知识库均不可用）。"

        tools.append(add_user_memory)

        @tool
        def search_knowledge(query: str) -> str:
            """检索伴侣（AI 角色）专属知识库（RAG 检索增强）。

            使用场景（必须优先使用本工具）：
            - 用户询问当前伴侣角色的喜好、设定、背景资料（如"小智喜欢吃什么""你的生日""你的设定"）
            - 用户询问伴侣知识库中的资料、笔记、文档内容

            不要使用本工具的场景：
            - 查用户本人的记忆、聊天历史、个人偏好 → 用 search_user_memory
            - 与用户个人记忆无关的通用问题

            Args:
                query: 检索查询语句

            Returns:
                检索到的知识片段
            """
            # 有 companionId 时优先调 8002 RAG 服务（远程知识库）
            if companion_id:
                try:
                    result = _search_knowledge_remote(companion_id, query, self.config)
                    if result is not None:
                        return result
                except Exception as e:
                    logger.warning("[search_knowledge] 8002 RAG 服务异常，回落本地: %s", e)

            # 本地 RAG 兜底
            try:
                from app.ai.rag import get_rag_store
                store = get_rag_store()
                if store is None:
                    return "知识库暂不可用。"
                docs = store.search(query, k=4)
                if not docs:
                    return "知识库中没有找到相关内容。"
                return "\n".join(d.page_content.strip() for d in docs if d.page_content.strip())
            except Exception as e:
                print("[search_knowledge] local fallback failed: " + str(e))
                return "知识库检索失败。"

        tools.append(search_knowledge)

        return tools

    def _build_messages(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        user_id: Optional[str] = None,
    ) -> List[Any]:
        """把 chat_history 转成 LangChain 消息类型"""
        messages: List[Any] = []

        for msg in (chat_history or [])[-12:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if not content:
                continue
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                messages.append(AIMessage(content=content))

        text = user_input
        if user_id:
            text = "[用户ID: " + user_id + "]\n" + user_input

        messages.append(HumanMessage(content=text))
        return messages

    @staticmethod
    def _extract_content(result: Any) -> str:
        """从 Agent 执行结果中提取最终回复文本"""
        if isinstance(result, dict):
            msgs = result.get("messages", [])
            for m in reversed(msgs):
                if isinstance(m, AIMessage):
                    content = m.content
                    if isinstance(content, list):
                        parts = []
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                parts.append(c.get("text", ""))
                            elif isinstance(c, str):
                                parts.append(c)
                        content = "".join(parts)
                    if content and str(content).strip():
                        return str(content)
        return str(result)

    def chat(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        personality: str = "温柔体贴",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """同步对话（含 Function Calling）"""
        try:
            messages = self._build_messages(user_input, chat_history, user_id)
            result = self.agent.invoke({"messages": messages})
            content = self._extract_content(result)
            return {
                "content": NaturalLanguageOutputParser.parse(content),
                "model": self.config.MODEL,
            }
        except Exception as e:
            print("[chat] error: " + str(e))
            return {
                "content": "抱歉，我这边出了点问题：" + str(e),
                "model": self.config.MODEL,
            }

    async def chat_stream(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        personality: str = "温柔体贴",
        user_id: Optional[str] = None,
        companion_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """流式对话（含 Function Calling）。

        Agent 执行完整链路后一次性拿到结果，再按块切分模拟流式输出，
        对前端表现为逐段吐字。

        有 companion_id 时构建带闭包的工具集 + agent（search_knowledge 优先调 8002），
        无 companion_id 时复用单例 agent。
        """
        try:
            # 有 companion_id 时按请求构建 agent（闭包绑定，并发安全）
            agent = self.agent
            if companion_id:
                tools = self._init_tools(companion_id=companion_id)
                agent = self._build_agent(tools)

            messages = self._build_messages(user_input, chat_history, user_id)
            result = await agent.ainvoke({"messages": messages})
            content = self._extract_content(result)
            parsed = NaturalLanguageOutputParser.parse(content)

            step = 8
            for i in range(0, len(parsed), step):
                yield parsed[i:i + step]
        except Exception as e:
            print("[chat_stream] error: " + str(e))
            yield "抱歉，我这边出了点问题：" + str(e)
