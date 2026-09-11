"""
LangChain ??? GLM ???
?? Function Calling???????RAG ?????????

???????????
1. ?? chat() ?? prompt | self.llm?tools ???????? LLM?
   ?????????"??????"???????????? -> ???
2. ???? LangChain 1.x ? create_agent() ????????? Agent?
   tools ??????????????????????????
3. ?? RAG ???? search_knowledge???????????
4. ?? chat() / chat_stream() ????????????????
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

# LangChain 1.x?AgentExecutor / create_tool_calling_agent ?????? create_agent
from langchain.agents import create_agent

# ????????????????????
try:
    from langchain_community.tools import DuckDuckGoSearchRun
    _WEB_SEARCH_AVAILABLE = True
except Exception:
    DuckDuckGoSearchRun = None
    _WEB_SEARCH_AVAILABLE = False

from app.ai.prompts import build_system_prompt


class NaturalLanguageOutputParser:
    """????????????? Markdown ??"""

    @staticmethod
    def parse(text: str) -> str:
        """?? Markdown ??????????"""
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


def create_glm_llm():
    """???? GLM ? LLM ???OpenAI ?????"""
    from app.ai.config import ZhipuAIConfig
    config = ZhipuAIConfig()

    if not config.is_valid():
        raise ValueError("?? API ?????API_KEY ???")

    return ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
        top_p=config.TOP_P,
    )


class LangChainGLMClient:
    """?? LangChain ????? GLM ?????? Function Calling + RAG?"""

    def __init__(self):
        from app.ai.config import ZhipuAIConfig
        self.config = ZhipuAIConfig()

        self.llm = create_glm_llm()
        self.tools = self._init_tools()

        # ???????????? Agent?tools ???????????
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=build_system_prompt(),
        )
        print("[LangChain] Agent ready, tools: " + str([t.name for t in self.tools]))

    def _init_tools(self) -> List[Any]:
        """????????Function Calling?"""
        tools: List[Any] = []

        if _WEB_SEARCH_AVAILABLE:
            try:
                tools.append(
                    DuckDuckGoSearchRun(
                        name="web_search",
                        description="?????????????????????????????",
                    )
                )
            except Exception as e:
                print("[LangChain] web_search init failed: " + str(e))

        @tool
        def search_user_memory(user_id: str, keyword: str) -> str:
            """???????????? + ???????

            Args:
                user_id: ??ID
                keyword: ?????

            Returns:
                ?????????????????
            """
            results: List[str] = []

            try:
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                if SessionLocal is not None:
                    with SessionLocal() as db:
                        memories = MemoryService(db).search_user_memory(user_id, keyword)
                        for m in memories or []:
                            results.append(str(m.keyword) + "?" + str(m.content))
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
                return "???????" + keyword + "?????"
            return "?".join(results)

        tools.append(search_user_memory)

        @tool
        def get_mood_history(user_id: str, days: int = 7) -> str:
            """????????????

            Args:
                user_id: ??ID
                days: ?????????7?

            Returns:
                ????????????????
            """
            try:
                from app.database import SessionLocal
                from app.services.memory_service import MoodService

                if SessionLocal is None:
                    return "??????????????????"

                with SessionLocal() as db:
                    moods = MoodService(db).get_mood_history(user_id, days)
                    if not moods:
                        return "??" + str(days) + "????????"
                    parts = []
                    for m in moods:
                        s = str(m.mood) + "?" + str(m.score) + "??"
                        if m.note:
                            s += "?" + str(m.note)
                        parts.append(s)
                    return "?".join(parts)
            except Exception as e:
                print("[get_mood_history] failed: " + str(e))
                return "??????????"

        tools.append(get_mood_history)

        @tool
        def add_user_memory(user_id: str, memory_type: str, content: str) -> str:
            """???????????????

            Args:
                user_id: ??ID
                memory_type: ?????fact / preference / birthday ??
                content: ??????

            Returns:
                ??????
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
                return "??????" + content
            return "??????????????????????"

        tools.append(add_user_memory)

        @tool
        def search_knowledge(query: str) -> str:
            """????????????RAG ??????

            ??????????????????????????

            Args:
                query: ????

            Returns:
                ????????
            """
            try:
                from app.ai.rag import get_rag_store
                store = get_rag_store()
                if store is None:
                    return "????????"
                docs = store.search(query, k=4)
                if not docs:
                    return "?????????????"
                return "\n".join(d.page_content.strip() for d in docs if d.page_content.strip())
            except Exception as e:
                print("[search_knowledge] failed: " + str(e))
                return "????????"

        tools.append(search_knowledge)

        return tools

    def _build_messages(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        user_id: Optional[str] = None,
    ) -> List[Any]:
        """??? chat_history ????? LangChain ????"""
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
            text = "[????ID: " + user_id + "]\n" + user_input

        messages.append(HumanMessage(content=text))
        return messages

    @staticmethod
    def _extract_content(result: Any) -> str:
        """? Agent ?????????????"""
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
        personality: str = "????",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """??????????? Function Calling?"""
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
                "content": "????????????????" + str(e),
                "model": self.config.MODEL,
            }

    async def chat_stream(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        personality: str = "????",
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """??????? Function Calling?

        ?? Agent ???????????????????????
        ??????????????????
        """
        try:
            messages = self._build_messages(user_input, chat_history, user_id)
            result = await self.agent.ainvoke({"messages": messages})
            content = self._extract_content(result)
            parsed = NaturalLanguageOutputParser.parse(content)

            step = 8
            for i in range(0, len(parsed), step):
                yield parsed[i:i + step]
        except Exception as e:
            print("[chat_stream] error: " + str(e))
            yield "??????????????" + str(e)
