"""
LangChain 封装的 GLM 客户端
支持 Function Calling 和流式响应
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.tools import tool
# 暂时移除复杂的Agent，改用简单实现
# from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import DuckDuckGoSearchRun

from app.ai.prompts import build_system_prompt


class NaturalLanguageOutputParser:
    """将输出解析为自然语言，移除Markdown格式"""

    @staticmethod
    def parse(text: str) -> str:
        """移除Markdown格式，转换为自然语言"""
        # 移除Markdown代码块
        text = text.replace("```", "").replace("``", "")

        # 移除可能的XML标记
        import re
        text = re.sub(r'<[^>]+>', '', text)

        # 移除Markdown标题
        lines = text.split("\n")
        processed_lines = []
        for line in lines:
            # 处理可能的格式化文本
            line = line.strip()

            if not line:
                processed_lines.append("")
                continue

            # 移除开头的#符号
            if line.startswith("#"):
                line = line.replace("#", "").strip()

            # 移除开头的标记符号
            while line.startswith(("*", "•", "-", "+")):
                line = line[1:].strip()

            # 移除行内格式标记
            line = line.replace("*", "").replace("**", "").replace("_", "")

            # 如果处理后的内容不为空，添加到结果
            if line:
                processed_lines.append(line)

        # 合并连续的空行
        result = []
        for line in processed_lines:
            if line.strip() == "":
                if result and result[-1].strip() != "":
                    result.append("")
            else:
                result.append(line)

        return "\n".join(result).strip()


def create_glm_llm():
    """
    独立的智谱 GLM LLM 实例创建方法

    封装所有配置逻辑，减少失误，便于维护

    Returns:
        ChatOpenAI: 已配置好的 LLM 实例
    """
    from app.ai.config import ZhipuAIConfig
    config = ZhipuAIConfig()

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
        from app.ai.config import ZhipuAIConfig
        self.config = ZhipuAIConfig()

        # 初始化 LangChain ChatOpenAI (使用独立的配置方法)
        self.llm = create_glm_llm()

        # 初始化工具
        self.tools = self._init_tools()

        # 构建提示词模板
        self.prompt = self._build_prompt_template()

    def _init_tools(self) -> List[Any]:
        """初始化工具函数 (Function Calling)"""

        # 联网搜索工具
        search_tool = DuckDuckGoSearchRun(
            name="web_search",
            description="搜索最新的网络信息，用于回答实时性问题、新闻、事件等"
        )

        @tool
        def search_user_memory(user_id: str, keyword: str) -> str:
            """
            搜索用户的记忆库

            Args:
                user_id: 用户ID
                keyword: 搜索关键词

            Returns:
                相关的记忆内容，格式化为自然语言描述
            """
            try:
                # 惰性导入数据库依赖，避免初始化时崩溃
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                # 检查数据库连接
                if SessionLocal is None:
                    return "抱歉，记忆系统暂时不可用（数据库未配置），但我可以基于对话内容回答您的问题。"

                with SessionLocal() as db:
                    service = MemoryService(db)
                    memories = service.search_user_memory(user_id, keyword)

                    if not memories:
                        return f"抱歉，我没有找到关于「{keyword}」的记忆。如果您希望我记住这个信息，请告诉我。"

                    # 将结果转换为自然语言描述
                    if len(memories) == 1:
                        memory = memories[0]
                        return f"我记得用户的一条关于「{memory.keyword}」的记忆：{memory.content}"
                    else:
                        result = f"我找到了{len(memories)}条关于「{keyword}」的记忆：\n"
                        for i, memory in enumerate(memories, 1):
                            result += f"{i}. {memory.keyword}：{memory.content}\n"
                        return result.strip()
            except Exception as e:
                print(f"[search_user_memory] 数据库查询失败: {e}")
                # 降级返回：让AI知道记忆系统暂时不可用
                return f"抱歉，记忆系统暂时不可用（{str(e)}），但我可以基于对话内容回答您的问题。"

        @tool
        def get_mood_history(user_id: str, days: int = 7) -> str:
            """
            获取用户最近的心情历史

            Args:
                user_id: 用户ID
                days: 查询最近几天，默认7天

            Returns:
                心情历史记录，格式化为自然语言描述
            """
            try:
                from app.database import SessionLocal
                from app.services.memory_service import MoodService

                # 检查数据库连接
                if SessionLocal is None:
                    return "抱歉，心情历史暂时不可用（数据库未配置），但我可以和您聊聊现在的心情。"

                with SessionLocal() as db:
                    service = MoodService(db)
                    moods = service.get_mood_history(user_id, days)

                    if not moods:
                        return f"用户 {user_id} 最近 {days} 天没有心情记录。"

                    # 将结果转换为自然语言描述
                    if len(moods) == 1:
                        mood = moods[0]
                        date_str = mood.created_at.strftime("%m-%d") if mood.created_at else "最近"
                        return f"用户在{date_str}的心情是{mood.mood}，心情分数{mood.score}分。{mood.note or ''}"
                    else:
                        result = f"用户最近{days}天的心情变化如下：\n"
                        for mood in moods:
                            date_str = mood.created_at.strftime("%m-%d") if mood.created_at else "未知日期"
                            result += f"• {date_str}: {mood.mood}（分数{mood.score}）{mood.note or ''}\n"
                        return result.strip()
            except Exception as e:
                print(f"[get_mood_history] 数据库查询失败: {e}")
                return f"抱歉，心情历史暂时无法获取（{str(e)}），但我们可以聊聊现在的心情。"

        @tool
        def add_user_memory(user_id: str, memory_type: str, content: str) -> str:
            """
            添加新的用户记忆

            Args:
                user_id: 用户ID
                memory_type: 记忆类型 (preference/重要日期/习惯/fact等)
                content: 记忆内容

            Returns:
                操作结果，格式化为自然语言描述
            """
            try:
                from app.database import SessionLocal
                from app.services.memory_service import MemoryService

                # 检查数据库连接
                if SessionLocal is None:
                    return "抱歉，记忆记录失败（数据库未配置），但我已经把您的话记在心里了。"

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
                    # 返回更友好的确认消息
                    return f"好的，我已经记住了：'{memory.content}'。这是属于{memory_type}类型的记忆。"
            except Exception as e:
                print(f"[add_user_memory] 数据库写入失败: {e}")
                return f"抱歉，记忆记录失败了（{str(e)}），但我已经把您的话记在心里了。"

        return [search_tool, search_user_memory, get_mood_history, add_user_memory]

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
        try:
            # 格式化聊天历史
            history_messages = self._format_chat_history(chat_history)

            # 构建输入
            input_text = user_input
            if user_id:
                input_text = f"[用户ID: {user_id}] {user_input}"

            # 构建提示
            prompt = ChatPromptTemplate.from_messages([
                ("system", build_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", input_text)
            ])

            # 创建链并执行
            chain = prompt | self.llm
            result = chain.invoke({
                "input": input_text,
                "chat_history": history_messages
            })

            # 使用输出解析器将Markdown转换为自然语言
            parsed_content = NaturalLanguageOutputParser.parse(result.content)

            return {
                "content": parsed_content,
                "model": self.config.MODEL
            }
        except Exception as e:
            print(f"[chat] 错误: {e}")
            return {
                "content": f"抱歉，处理您的请求时出现了错误：{str(e)}",
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

        Args:
            user_input: 用户输入
            chat_history: 聊天历史
            personality: AI 性格
            user_id: 用户ID

        Yields:
            流式返回的文本片段
        """
        try:
            # 格式化聊天历史
            history_messages = self._format_chat_history(chat_history)

            # 构建输入
            input_text = user_input
            if user_id:
                input_text = f"[用户ID: {user_id}] {user_input}"

            # 构建提示
            prompt = ChatPromptTemplate.from_messages([
                ("system", build_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", input_text)
            ])

            # 创建流式链
            chain = prompt | self.llm | StrOutputParser()

            async for chunk in chain.astream({
                "input": input_text,
                "chat_history": history_messages
            }):
                # 对每个chunk进行解析，去除Markdown格式
                parsed_chunk = NaturalLanguageOutputParser.parse(chunk)
                yield parsed_chunk

        except Exception as e:
            print(f"[chat_stream] 错误: {e}")
            yield f"抱歉，流式处理时出现了错误：{str(e)}"

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
