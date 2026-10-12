# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 情侣互动产品（AI Companion）：AI 陪伴聊天应用，前后端分离，四个独立服务。产品、文档和代码注释均以简体中文为主。

## 服务与端口

| 服务 | 目录 | 端口 | 技术栈 |
| --- | --- | --- | --- |
| 前端 | `frontend/` | 3000 | Vue 3 + TypeScript + Vite 5 + Pinia + Tailwind CSS |
| Python AI 服务 | `backend/` | 5000 | FastAPI + 双模型（MiMo 文本 / GPTCODEX 视觉）+ LangChain 1.x |
| Java 业务后端 | `backend-java/` | 8080 | Spring Boot 3 + MyBatis Plus + MySQL |
| RAG 知识库 | `RAG-Knowledge-System/backend/` | 8002 | FastAPI + Chroma 向量库 |

注意：根目录 `README.md` 写的后端端口 8000 已过时，实际为 5000（前端硬编码、`main.py` 的 `APP_PORT` 默认值均为 5000）。

## 常用命令

```bash
# 前端
cd frontend
npm install
npm run dev        # 开发服务器，端口 3000
npm run build      # vue-tsc --noEmit 类型检查 + 打包
npm run check      # 仅 TypeScript 类型检查
npm run lint       # ESLint（lint:fix 自动修复）

# Python AI 服务
cd backend
pip install -r requirements.txt
python init_db.py  # 建表（支持 SQLite/PostgreSQL，逐表创建、失败跳过）
python main.py     # 或 uvicorn main:app --reload --port 5000

# Java 业务后端
cd backend-java
mvn clean install
mvn spring-boot:run   # Swagger: http://localhost:8080/doc.html

# RAG 知识库服务
cd RAG-Knowledge-System/backend
pip install -r requirements.txt
python main.py        # API 文档: http://localhost:8002/docs
```

测试：Python 测试为 pytest 风格（`backend/tests/test_*.py`，pytest 未列入 requirements，需单独 `pip install pytest`）；单个测试用 `pytest tests/test_prompts.py::测试函数名`。Java 与 RAG 服务当前无测试代码。

## 架构要点

### 前端与后端的实际连接（重点）

前端目前只有两处真实调用后端，全部硬编码 `http://localhost:5000`，没有 Vite 代理、没有 `.env`：

- `frontend/src/composables/useStreamingChat.ts` — AI 流式聊天与快捷建议
- `frontend/src/pages/CreatePage.vue` — AI 头像生成

其余业务（登录注册、伴侣列表、聊天记录、记忆管理、情绪日历）都是 **Pinia store 内的 mock 数据 + localStorage**，未接后端。Java 业务后端（8080）已实现完整 REST API，但前端尚未接入；它通过 `application.yml` 中 `url: http://localhost:5000` 调用 Python AI 服务。

### Python AI 服务（backend/）

- `backend/main.py` 是单文件大入口：全部路由（聊天、流式、建议、头像、LangChain 聊天、记忆、心情、性能指标）都定义在这里。
- **三层降级链**：LangChain 客户端 → OpenAI SDK 直连 → 预设回复库 `PRESET_RESPONSES`。任一层失败自动落到下一层，服务永不因 API 故障挂掉。
- **双模型架构**（2026-10 起，全面移除智谱链路）：文本链路走小米 MiMo（`mimo-v2.6-flash`），带图片的请求路由到视觉链路 GPTCODEX 中转站（`gpt-6-luna`）；`LLM_IMAGE_MODEL` 置空时头像走本地 SVG 降级。两平台均 OpenAI 兼容协议，客户端为 `openai.OpenAI`。普通对话传 `extra_body={"thinking":{"type":"disabled"}}` 降延迟，LangChain 链路保留思考。
- **Redis 可选**：启动时探测，不可用则降级为进程内内存缓存（会话缓存 + 响应缓存）。
- `app/ai/` 是 AI 核心模块：`langchain_client.py`（LangChain 1.x `create_agent` Function Calling，工具包括 `web_search`、`search_user_memory`、`add_user_memory`、`get_mood_history`、`search_knowledge`）、`rag.py`（Chroma 向量检索 + 本地哈希向量 Embedding——两平台均无 Embedding 端点；向量库存于 `backend/chroma_db/`）、`prompts.py`（系统提示词/头像提示词构建）、`config.py`（`LLMConfig` 双链路配置）、`avatar_store.py`。
- `app/models/` 为 SQLAlchemy ORM 模型；`app/services/memory_service.py` 封记了记忆/心情 CRUD。`app/database.py` 在连接失败时将 engine 置为 `None` 并告警——此时记忆类接口返回 503，但 AI 聊天仍可用。

### 接口约定

- 请求体 `ChatRequest`：`{ systemPrompt, messages[{role,content,images?}], userMessage, images?, userId? }`（images 为 base64 data URL）。
- 统一响应包装 `APIResponse`：`{ success, message, data, timestamp }`。
- SSE 流式格式：每行 `data: {"delta": "文本", "done": false}\n\n`，结束帧 `{"delta": "", "done": true}`；前端按 `data: ` 前缀逐行解析。
- 关键端点：`/api/v1/ai/chat/stream`（普通流式）、`/api/v1/ai/chat/langchain/stream`（RAG + Function Calling 增强流式）、`/api/v1/ai/suggestions`、`/api/v1/memory/{user_id}`、`/api/v1/mood/{user_id}`。

### 前端结构

- 页面在 `frontend/src/pages/`，路由见 `src/router/index.ts`；`@` 别名指向 `src/`（`vite.config.ts`）。
- `ChatPage.vue` 是核心页面：`enableRAG` 开关（默认开启）决定调用 LangChain 流式端点还是普通端点；聊天状态在 `stores/chat.ts`，伴侣数据在 `stores/companion.ts`。

## 配置

- `backend/.env`（已被 gitignore）：双链路变量 `LLM_MODEL_API_KEY`/`LLM_MODEL_BASE_URL`/`LLM_MODEL_MODEL`（文本 MiMo）、`LLM_VISION_API_KEY`/`LLM_VISION_BASE_URL`/`LLM_VISION_MODEL`（视觉 GPTCODEX）、`LLM_IMAGE_MODEL`（置空走 SVG 降级）、`LLM_TEMPERATURE`/`LLM_MAX_TOKENS`/`LLM_TOP_P`，另有 `DATABASE_URL`（SQLite 或 PostgreSQL）、`REDIS_URL`、`APP_HOST`/`APP_PORT`/`APP_DEBUG`。键名清单见 `backend/.env.example`。密钥只写 `.env`，文档一律 `sk-***` 占位。
- `AI_INTEGRATION.md` 中含有明文 API 密钥，不要将其复制进代码、提交记录或对外发布的文档。
- `.gitignore` 已忽略 `.env`、`chroma_db/`、`ai_companion.db`、`*.tmp` 等运行时/密钥文件。

## 文档

- `docs/后端技术文档.md` — 后端实现细节（数据库表结构、接口）
- `docs/03-API接口文档.md` — API 规范
- `docs/LANGCHAIN_MIGRATION_GUIDE.md` — LangChain 集成与 RAG 说明，但该文件为 GBK 编码，按 UTF-8 读取会乱码，需转码后再读
- `docs/前端技术文档.md`、`docs/AI聊天功能优化方案.md`、`docs/功能上线排期指南.md`
