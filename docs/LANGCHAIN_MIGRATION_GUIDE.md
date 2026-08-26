# LangChain 迁移与使用指南

## 📋 概述

项目已成功集成 LangChain 框架，提供以下增强功能：

- **Function Calling (工具调用)**：支持记忆查询、心情历史查询等功能
- **Agent 架构**：智能 Agent 自动选择何时调用工具
- **向后兼容**：保留原有接口，同时新增 LangChain 专属接口
- **降级机制**：LangChain 不可用时自动回退到原有实现

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

新增的主要依赖：
- `langchain` - 核心框架
- `langchain-openai` - OpenAI 兼容接口（适配智谱 GLM）
- `langchain-community` - 社区工具集成

### 2. 配置环境变量

确保 `.env` 文件中包含：

```env
ZHIPU_API_KEY=your_api_key_here
ZHIPU_MODEL=glm-4.5-air
REDIS_URL=redis://localhost:6379/1

# 数据库（记忆系统必需，开发环境默认 SQLite）
DATABASE_URL=sqlite:///./ai_companion.db
# PostgreSQL: postgresql://user:password@localhost:5432/ai_companion
# MySQL:      mysql+pymysql://user:password@localhost:3306/ai_companion
```

### 3. 初始化数据库表

```bash
cd backend
python init_db.py
```

这会自动创建所有数据表（users、conversations、messages、companions、user_memories、user_moods 等）。

### 4. 启动服务

```bash
cd backend
python main.py
```

启动成功后，你会看到：
```
Successfully initialized Zhipu AI client...
Successfully initialized LangChain client...
```

## 📡 API 接口

### 原有接口（保持不变）

| 接口 | 说明 |
|------|------|
| `POST /api/v1/ai/chat` | 普通聊天接口 |
| `POST /api/v1/ai/chat/stream` | 流式聊天接口 |
| `POST /api/v1/ai/generate-avatar` | 头像生成接口 |

### 新增 LangChain 接口

| 接口 | 说明 |
|------|------|
| `POST /api/v1/ai/chat/langchain` | LangChain 聊天（支持 Function Calling） |
| `POST /api/v1/ai/chat/langchain/stream` | LangChain 流式聊天 |

### 新增 记忆与心情管理接口

| 接口 | 说明 |
|------|------|
| `GET /api/v1/memory/{user_id}` | 查询用户记忆（可选 `?keyword=` 过滤） |
| `POST /api/v1/memory` | 添加用户记忆 |
| `GET /api/v1/mood/{user_id}` | 查询心情历史（可选 `?days=7`） |
| `POST /api/v1/mood` | 记录用户心情 |

> LangChain 聊天接口现在支持 `userId` 字段。传入后，AI Agent 会自动通过 Function Calling 查询该用户的记忆库和心情历史，实现"有记忆的对话"。

## 🧪 测试示例

### 测试 LangChain 普通聊天

```bash
curl -X POST "http://localhost:5000/api/v1/ai/chat/langchain" \
-H "Content-Type: application/json" \
-d '{
  "userMessage": "你好，我叫小明",
  "systemPrompt": "你是一个温柔体贴的AI伴侣",
  "messages": []
}'
```

### 测试 Function Calling（记忆查询）

```bash
curl -X POST "http://localhost:5000/api/v1/ai/chat/langchain" \
-H "Content-Type: application/json" \
-d '{
  "userMessage": "你还记得我叫什么名字吗？",
  "systemPrompt": "你是一个温柔体贴的AI伴侣",
  "userId": "user-001",
  "messages": []
}'
```

传入 `userId` 后，AI 会自动调用 `search_user_memory` 工具查询该用户的记忆库。

### 先添加记忆，再查询

```bash
# 1. 添加一条记忆
curl -X POST "http://localhost:5000/api/v1/memory" \
-H "Content-Type: application/json" \
-d '{
  "userId": "user-001",
  "memoryType": "fact",
  "content": "用户叫小明，生日是5月20日"
}'

# 2. 带记忆聊天
curl -X POST "http://localhost:5000/api/v1/ai/chat/langchain" \
-H "Content-Type: application/json" \
-d '{
  "userMessage": "你知道我的生日吗？",
  "userId": "user-001",
  "messages": []
}'
```

### 测试心情历史查询

```bash
curl -X POST "http://localhost:5000/api/v1/mood" \
-H "Content-Type: application/json" \
-d '{
  "userId": "user-001",
  "mood": "开心",
  "score": 8.5,
  "note": "今天和AI聊天很愉快"
}'

curl -X POST "http://localhost:5000/api/v1/ai/chat/langchain" \
-H "Content-Type: application/json" \
-d '{
  "userMessage": "我最近心情怎么样？",
  "userId": "user-001",
  "messages": []
}'
```

### 测试流式响应

```javascript
// 使用 JavaScript EventSource
const eventSource = new EventSource('http://localhost:5000/api/v1/ai/chat/langchain/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    userMessage: "你好呀",
    systemPrompt: "你是一个温柔体贴的AI伴侣",
    messages: []
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.delta) {
    console.log(data.delta); // 逐字打印
  }
  if (data.done) {
    eventSource.close();
  }
};
```

## 🔧 架构详解

### 新增文件结构

```
backend/
├── app/
│   ├── ai/
│   │   ├── prompts.py           # 提示词构建（原有）
│   │   ├── glm_client.py        # 原生 GLM 客户端（原有）
│   │   └── langchain_client.py  # LangChain 客户端（工具已接真实数据库）
│   ├── models/
│   │   ├── user.py              # 用户模型
│   │   ├── chat.py              # 对话模型
│   │   ├── companion.py         # AI 伴侣模型
│   │   └── memory.py            # 新增：记忆与心情模型
│   ├── services/
│   │   └── memory_service.py    # 新增：记忆/心情 CRUD 服务
│   ├── database.py              # 数据库连接（含容错降级）
│   └── config.py                # 配置（新增 DATABASE_URL）
├── init_db.py                   # 新增：一键建表脚本
├── main.py                       # 集成更新（新增记忆/心情 API）
└── requirements.txt              # 新增依赖
```

### LangChain 客户端 (`langchain_client.py`)

```
┌─────────────────────────────────────────────────────────────┐
│                    LangChainGLMClient                        │
├─────────────────────────────────────────────────────────────┤
│  - llm: ChatOpenAI (兼容智谱 GLM API)                       │
│  - tools: List[Tool]                                         │
│  - agent: AgentExecutor                                      │
│  - prompt: ChatPromptTemplate                                │
├─────────────────────────────────────────────────────────────┤
│  + chat(): Dict         # 普通聊天（含工具调用）            │
│  + chat_stream(): AsyncGenerator  # 流式聊天                │
│  - _init_tools(): List  # 初始化工具（记忆查询等）          │
│  - _build_prompt(): Template  # 构建提示词                  │
│  - _format_history(): List  # 格式化历史消息                 │
└─────────────────────────────────────────────────────────────┘
```

### 工具列表 (Function Calling)

| 工具名称 | 功能 | 数据来源 |
|---------|------|---------|
| `search_user_memory(user_id, keyword)` | 搜索用户记忆库 | `user_memories` 表 |
| `get_mood_history(user_id, days)` | 获取用户心情历史 | `user_moods` 表 |
| `add_user_memory(user_id, memory_type, content)` | 添加用户记忆 | 写入 `user_memories` 表 |

> ✅ 工具已对接真实数据库（通过 `MemoryService` / `MoodService`）。当数据库不可用时，工具会优雅降级返回提示，不影响对话进行。

### 降级策略

```
用户请求
  ├─→ LangChain 可用？
  │    ├─是 → 使用 Agent 执行
  │    │         └─→ 失败？ → 继续降级
  │    └─否 → 使用原有的 zhipu_client
  │               └─→ 失败？ → 使用预设回复
  └─→ 返回结果
```

## 📚 扩展开发

### 添加新的工具 (Function Calling)

在 `langchain_client.py` 的 `_init_tools()` 方法中添加：

```python
@tool
def my_new_tool(param: str) -> str:
    """工具描述（AI 会读取这个描述来决定何时调用）"""
    # 你的逻辑
    return "工具返回结果"
```

然后将其添加到返回的工具列表中：

```python
return [search_user_memory, get_mood_history, my_new_tool]
```

### 连接真实数据库（已实现 ✅）

工具已对接真实数据库。实现方式是在工具函数内部惰性导入 `SessionLocal`，并通过 `MemoryService` / `MoodService` 操作数据库：

```python
@tool
def search_user_memory(user_id: str, keyword: str) -> str:
    """搜索用户记忆库"""
    try:
        from app.database import SessionLocal
        from app.services.memory_service import MemoryService

        if SessionLocal is None:
            return "记忆系统暂时不可用（数据库未配置）。"

        with SessionLocal() as db:
            service = MemoryService(db)
            memories = service.search_user_memory(user_id, keyword)
            # ... 格式化返回
    except Exception as e:
        return f"记忆系统暂时不可用（{e}）。"
```

这种设计的好处：
- **惰性导入**：数据库依赖在工具调用时才加载，服务启动不依赖数据库
- **优雅降级**：数据库不可用时工具返回提示文本，AI 仍能正常对话
- **请求隔离**：每次调用创建独立 session，避免并发问题

### 使用 RAG (检索增强生成)

后续扩展步骤：

1. 添加文档加载器
2. 集成向量化模型 (智谱 Embedding)
3. 添加向量数据库 (Chroma / Milvus)
4. 构建 RAG Chain

```python
# 示例
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

vectorstore = Chroma.from_documents(docs, embeddings)
rag_chain = (
    {"context": vectorstore.as_retriever(), "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

## 🔍 调试技巧

### 启用详细日志

在 `main.py` 中设置：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 使用 LangSmith (可选)

在 `.env` 中配置：

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=ai-companion
```

## ✅ 验证清单

- [x] 服务正常启动，无报错（数据库未配置时也能启动，仅记忆功能不可用）
- [x] 看到 LangChain 初始化成功日志
- [ ] 普通聊天接口返回正常
- [ ] Function Calling 触发成功（需配置 DATABASE_URL 并运行 `init_db.py`）
- [ ] 流式接口逐字返回
- [ ] 降级机制工作正常

## 📝 注意事项

1. **向后兼容**：原有接口继续工作，推荐逐步迁移
2. **Token 控制**：LangChain Agent 可能消耗更多 Token
3. **异步处理**：新流式接口使用 AsyncGenerator，性能更好
4. **Redis 依赖**：会话缓存依赖 Redis，确保 Redis 可用
5. **数据库类型兼容**：项目模型使用了 PostgreSQL 特有的 `UUID` 和 `ARRAY` 类型。若使用 MySQL/SQLite，需将模型中 `UUID(as_uuid=True)` 改为 `String(36)`，`ARRAY(String)` 改为 `JSON` 或 `Text`
6. **流式模式限制**：流式接口（`chat_stream`）使用简单 Chain 而非 AgentExecutor，因此流式模式下 Function Calling 不可用。需要工具调用时请使用非流式接口 `/api/v1/ai/chat/langchain`

## 🔗 相关资源

- [LangChain 官方文档](https://python.langchain.com/)
- [智谱 AI 文档](https://open.bigmodel.cn/dev/api)
- [项目架构文档](./01-项目架构设计文档.md)
