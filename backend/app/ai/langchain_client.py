"""
LangChain 封装的 GLM 客户端
支持 Function Calling 和流式响应
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent

from app.ai.prompts import build_system_prompt
from app.ai.config import get_zhipu_config


def create_glm_llm():
    """
    独立的智谱 GLM LLM 实例创建方法

    封装所有配置逻辑，减少失误，便于维护

    Returns:
        ChatOpenAI: 已配置好的 LLM 实例
    """
    config = get_zhipu_config()

    # 验证配置
    if not config.is_valid():
        raise ValueError("智谱 API 配置无效：API_KEY 未设置")

    # 创建兼容 OpenAI 格式的 LLM
    llm = ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
        top_p=config.TOP_P,
    )

    return llm


class LangChainGLMClient:
    """使用 LangChain 封装的智谱 GLM 客户端"""

    def __init__(self):
        # 获取配置
        self.config = get_zhipu_config()

        # 初始化 LangChain ChatOpenAI (使用独立的配置方法)
        self.llm = create_glm_llm()

        # 初始化工具
        self.tools = self._init_tools()

        # 构建提示词模板
        self.prompt = self._build_prompt_template()

        # 初始化 Agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )

    def _init_tools(self) -> List[Any]:
        """初始化工具函数 (Function Calling)"""

        @tool
        def search_user_memory(user_id: str, keyword: str) -> str:
            """
            搜索用户的记忆库

            Args:
                user_id: 用户ID
                keyword: 搜索关键词

            Returns:
                相关的记忆内容
            """
            try:
                # 惰性导入数据库依赖，避免初始化时崩溃
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                if SessionLocal is None:
                    return "记忆系统暂时不可用（数据库未配置）。"

                with SessionLocal() as db:
                    service = MemoryService(db)
                    memories = service.search_user_memory(user_id, keyword)

                    if not memories:
                        return f"没有找到关于「{keyword}」的记忆。"

                    results = []
                    for m in memories:
                        results.append(f"- [{m.memory_type}] {m.keyword}: {m.content}")
                    return "\n".join(results)
            except Exception as e:
                print(f"[search_user_memory] 数据库查询失败: {e}")
                # 降级返回：让AI知道记忆系统暂时不可用
                return f"记忆系统暂时不可用（{str(e)}），请直接根据对话上下文回复。"

        @tool
        def get_mood_history(user_id: str, days: int = 7) -> str:
            """
            获取用户最近的心情历史

            Args:
                user_id: 用户ID
                days: 查询最近几天，默认7天

            Returns:
                心情历史记录
            """
            try:
                from app.database import SessionLocal
                from app.services.memory_service import MoodService

                if SessionLocal is None:
                    return "心情历史暂时不可用（数据库未配置）。"

                with SessionLocal() as db:
                    service = MoodService(db)
                    moods = service.get_mood_history(user_id, days)

                    if not moods:
                        return f"用户 {user_id} 最近 {days} 天没有心情记录。"

                    results = []
                    for m in moods:
                        date_str = m.created_at.strftime("%m-%d") if m.created_at else "未知日期"
                        results.append(f"- {date_str}: {m.mood}(分数{m.score}) {m.note or ''}")
                    return f"用户最近 {days} 天的心情记录：\n" + "\n".join(results)
            except Exception as e:
                print(f"[get_mood_history] 数据库查询失败: {e}")
                return f"心情历史暂时无法获取（{str(e)}），请直接根据对话上下文回复。"

        @tool
        def add_user_memory(user_id: str, memory_type: str, content: str) -> str:
            """
            添加新的用户记忆

            Args:
                user_id: 用户ID
                memory_type: 记忆类型 (preference/重要日期/习惯/fact等)
                content: 记忆内容

            Returns:
                操作结果
            """
            try:
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                if SessionLocal is None:
                    return "记忆记录失败（数据库未配置），但你可以继续对话。"

                with SessionLocal() as db:
                    service = MemoryService(db)
                    # keyword 从 content 中提取前20字作为关键词
                    keyword = content[:20] if len(content) <= 20 else content[:20] + "..."
                    memory = service.add_user_memory(
                        user_id=user_id,
                        memory_type=memory_type,
                        keyword=keyword,
                        content=content
                    )
                    return f"已成功记录：{memory.content}"
            except Exception as e:
                print(f"[add_user_memory] 数据库写入失败: {e}")
                return f"记忆记录失败（{str(e)}），但你可以继续对话。"

        return [search_user_memory, get_mood_history, add_user_memory]

    def _build_prompt_template(self) -> ChatPromptTemplate:
        """构建提示词模板"""
        system_prompt = build_system_prompt()

        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    def chat(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        personality: str = "温柔体贴",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        普通聊天对话（非流式）

        Args:
            user_input: 用户输入
            chat_history: 聊天历史
            personality: AI 性格
            user_id: 用户ID（用于记忆查询）

        Returns:
            AI 回复结果
        """
        # 格式化聊天历史
        history_messages = self._format_chat_history(chat_history)

        # 构建输入，包含用户ID以便Agent传递给工具
        input_text = user_input
        if user_id:
            input_text = f"[用户ID: {user_id}] {user_input}"

        # 调用 Agent
        response = self.agent_executor.invoke({
            "input": input_text,
            "chat_history": history_messages
        })

        return {
            "content": response["output"],
            "model": self.config.MODEL
        }

    async def chat_stream(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
        personality: str = "温柔体贴",
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天对话

        注意：流式模式使用简单 Chain 而非 AgentExecutor，
        因此 Function Calling 在流式模式下不可用。
        如需在流式模式下使用工具，建议先调用非流式接口获取工具结果，
        再使用流式接口生成最终回复。

        Args:
            user_input: 用户输入
            chat_history: 聊天历史
            personality: AI 性格
            user_id: 用户ID

        Yields:
            流式返回的文本片段
        """
        # 对于流式输出，我们先使用简单的链式调用
        # Agent 的流式调用会稍微复杂一些
        prompt = ChatPromptTemplate.from_messages([
            ("system", build_system_prompt(personality)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        history_messages = self._format_chat_history(chat_history)

        input_text = user_input
        if user_id:
            input_text = f"[用户ID: {user_id}] {user_input}"

        async for chunk in chain.astream({
            "input": input_text,
            "chat_history": history_messages
        }):
            yield chunk

    def _format_chat_history(self, chat_history: Optional[List[Dict]]) -> List:
        """格式化聊天历史为 LangChain 消息格式"""
        if not chat_history:
            return []

        messages = []
        for msg in chat_history[-12:]:  # 保留最近12条
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                messages.append(AIMessage(content=content))

        return messages
