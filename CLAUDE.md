# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 情侣互动产品（AI Companion）：AI 陪伴聊天应用，前后端分离，四个独立服务。产品、文档和代码注释均以简体中文为主。

## 服务与端口

| 服务 | 目录 | 端口 | 技术栈 |
| --- | --- | --- | --- |
| 前端 | `frontend/` | 3000 | Vue 3 + TypeScript + Vite 5 + Pinia + Tailwind CSS |
| Python AI 服务 | `backend/` | 5000 | FastAPI + 智谱 GLM（glm-4.5-air 文本 / glm-4v-flash 视觉 / cogview-4 图像）+ LangChain 1.x |
| Java 业务后端 | `backend-java/` | **8081** | Spring Boot 3 + MyBatis Plus + MySQL |
| RAG 知识库 | `RAG-Knowledge-System/backend/` | 8002 | FastAPI + **Milvus 2.6.0（默认）+ TEI rerank**；Chroma 保留为回退 |

> **端口口径已闭环（2026-11-15 任务八）**：本机 8080 被无关项目 `xiaoyi-rag-server` 长期占用，Java 固定 **8081**，已写入 `backend-java/src/main/resources/application.yml`（`server.port` 与 `app.upload.base-url`），不再依赖启动参数覆盖。

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
python -m uvicorn main:app --host 0.0.0.0 --port 5000
# ⚠ 不要用 python main.py：APP_DEBUG=true 会开 reload，kill 父进程后
#   multiprocessing 子进程仍占 5000，新进程绑定失败 exit code 3

# Java 业务后端
cd backend-java
mvn clean install
mvn spring-boot:run   # Swagger: http://localhost:8081/doc.html（端口已在 yml 固定）

# RAG 知识库服务
cd RAG-Knowledge-System/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8002

# 一键启停（推荐）：四个服务统一走同一套 Start-Process + 重定向逻辑
powershell -NoProfile -File scripts/start-all.ps1
powershell -NoProfile -File scripts/stop-all.ps1    # 按端口反查进程树，含 Java 8081
powershell -NoProfile -File scripts/start-all.ps1 -Service 8081   # 只启单个服务
```

**日志口径（2026-11-16 收口）**：统一写 `logs/<name>.out.log` / `<name>.error.log`，name ∈ `frontend-3000` / `ai-5000` / `java-8081` / `rag-8002`。**每次启动前把旧日志归档**为 `<name>.<stream>.<时间戳>.log`（因为 `Start-Process -RedirectStandardOutput` 会截断目标文件，不归档就会丢上次输出），每个服务每种流保留最近 5 个归档，超出自动删除。历史日志在 `logs/archive/`。

> ⚠ 不要在 bash 里拼 `-RedirectStandardOutput "D:\path\\$VAR"`：bash 双引号会把 `\\` 折成 `\` 且把 `$VAR` 展开成空串，得到畸形路径（`D:\Ai_robotchat$VAR`），日志写到项目根目录且文件名不对——看起来像「重定向不生效」，实际是路径拼错。

测试：Python 测试为 pytest 风格（`backend/tests/test_*.py`，pytest 未列入 requirements，需单独 `pip install pytest`）；单个测试用 `pytest tests/test_prompts.py::测试函数名`。`tests/manual_rag_tool_test.py` 是手动回归脚本（需 5000/8002 在线），pytest 不收集。Java 与 RAG 服务当前无自动化测试。

## 架构要点

### 前端与后端的实际连接（重点，2026-11-15）

**前端已接 Java 8081，业务数据全部走后端**（任务三/四/五完成），统一 API 层在 `frontend/src/lib/api.ts`（`javaFetch` / `aiFetch` / `unwrapJava` / `unwrapPython`），地址走 `.env.development`，源码零硬编码。

三条出站链路：

- `lib/api.ts` → Java 8081：登录注册、伴侣、会话消息、图片上传、头像代理、记忆/情绪（任务四起记忆/情绪改调 Python）
- `composables/useStreamingChat.ts` → Python 5000：SSE 流式聊天（唯一业务直连），请求头带 `X-Service-Token`，body 带 `companionId`
- `lib/api.ts` `aiFetch` → Python 5000：`/api/v1/memory/*`、`/api/v1/mood/*`

流式结束后 `chatStore.saveMessages()` 用 `generate=false` 把 user+assistant 两条落库到 Java（P0-5 方案 A）。Java 通过 `application.yml` 的 `ai.service.url: http://localhost:5000` 调用 Python。

### Python AI 服务（backend/）

- `backend/main.py` 是单文件大入口：全部路由（聊天、流式、建议、头像、LangChain 聊天、记忆、心情、性能指标）都定义在这里。
- **三层降级链**：LangChain 客户端 → OpenAI SDK 直连 → 预设回复库 `PRESET_RESPONSES`。任一层失败自动落到下一层，服务永不因 API 故障挂掉。
- **单平台三链路**（2026-11-13 定稿为智谱 GLM 单平台）：文本 `glm-4.5-air`、视觉 `glm-4v-flash`、图像生成 `cogview-4`，共用 `ZHIPU_API_KEY`，base URL 均为 `https://open.bigmodel.cn/api/paas/v4`，客户端为 `openai.OpenAI`。`ZHIPU_IMAGE_MODEL` 置空时头像走本地 SVG 降级。**`glm-4.5-air` 是思考模型，普通对话必须传 `extra_body={"thinking":{"type":"disabled"}}`，否则 `max_tokens` 较小时 `content` 为空**；LangChain 链路保留思考。带图请求绕过 LangChain Agent 直接走视觉链路（Agent 的 `HumanMessage` 无法承载 `image_url`）。
- **Redis 可选**：启动时探测，不可用则降级为进程内内存缓存（会话缓存 + 响应缓存）。
- `app/ai/` 是 AI 核心模块：`langchain_client.py`（LangChain 1.x `create_agent` Function Calling，工具包括 `web_search`、`search_user_memory`、`add_user_memory`、`get_mood_history`、`search_knowledge`）、`rag.py`（Chroma 向量检索 + 本地哈希向量 Embedding——未接入远程 Embedding API；向量库存于 `backend/chroma_db/`）、`prompts.py`（系统提示词/头像提示词构建）、`config.py`（`LLMConfig` 配置，字段名 `API_KEY`/`MODEL`/`VISION_*` 映射自 `ZHIPU_*` 环境变量，另有 `RAG_SERVICE_URL`/`RAG_TIMEOUT`）、`avatar_store.py`。
- **RAG 双路（P1-1 已完成）**：`search_knowledge` 优先调 8002 `/api/v1/kb/retrieve`（`{companionId, query, topK}`），**只在超时/异常/5xx 时回落本地 RAGStore**；8002 返回空 chunks 是正常业务结果，不回落。有 `companionId` 时每次请求构建新 agent（闭包绑定，并发安全），无则复用单例。
- **工具选择规则（2026-11-15 修复）**：用户本人记忆/聊天历史 → `search_user_memory`；伴侣角色喜好/设定/背景 → `search_knowledge`。改提示词时双向都要测，避免把偏见从一侧翻到另一侧。
- `app/models/` 为 SQLAlchemy ORM 模型；`app/services/memory_service.py` 封记了记忆/心情 CRUD。`app/database.py` 在连接失败时将 engine 置为 `None` 并告警——此时记忆类接口返回 503，但 AI 聊天仍可用。

### RAG 知识库服务（RAG-Knowledge-System/backend/）

- 独立 FastAPI 服务（8002）：知识库/文档/切片/检索 API，元数据存 MySQL `rag_knowledge` 库。
- **向量存储（2026-11-21 验收后口径）**：默认 **Milvus 2.6.0** 单集合 `kb_chunks`，`companion_id/collection_id/document_id` 均为 **VARCHAR(36)**（业务 ID 是 32 位无连字符 UUID 或 `preset-*`），Partition Key = `companion_id`；dense 向量由 **Milvus 服务端 Function 调智谱 embedding-3（2048 维）**生成，8002 只传文本。**Chroma（`storage/chroma_db/`，本地哈希 256 维）仅作回退，代码与依赖保留未删**。切换入口 `get_vector_store()`，开关 `VECTOR_STORE_BACKEND=milvus|chroma`。
- **检索链路**：`retrieve` 路由必须是**普通 `def` 而非 `async def`**——底层 pymilvus `collection.search` 是同步阻塞，实测 async 下慢检索会阻塞事件循环导致 `/health` 无响应。
- **rerank**：TEI 自托管 `bge-reranker-v2-m3`（容器名 `milvus-tei`，Milvus 容器视角 `http://tei:80`）。**Milvus v2.6.0 的 rerank deadline 源码硬编码 30s，不可配置**；CPU 推理约 24ms/字，4 候选约 22–26s，**当前性能不达标（远超 3s 预算）**，详见 `docs/RAG知识库数据导入验收报告.md`。
- **鉴权（Phase 2 第一、二批已完成，2026-11-21）**：`/retrieve` 用 `X-Service-Token`（与 5000 的 `SERVICE_TOKEN` 同值）；**其余 15 个管理路由全部要求 `Authorization: Bearer <JWT>` 并做归属校验**，白名单仅 `/health`、`/`、`/api/v1/auth/login`。`tests/test_auth_coverage.py` 断言防漏挂。
  - **铁律**：归属判断的唯一身份来源是 JWT 的 `userId`，禁止信任请求体/查询参数中的自称身份。
  - **错误码**：401 未认证 / **403 无权（含不存在，防探测）** / **503 主库不可用**（不得伪装成 403）/ 400 参数非法。
  - **JWT 与 Java 同源**：8002 只读用户级环境变量 `JWT_SECRET`，`.env` 里**不得**再写 `JWT_SECRET_KEY`（`config.py` 用 `AliasChoices("JWT_SECRET", ...)` 显式绑定）。启动自检打印密钥**指纹前 8 位**，读到默认值或与 Java 兜底密钥一致时**直接启动失败**。
  - **算法（2026-11-22 加固）**：Java 显式 `signWith(key, Jwts.SIG.HS512)`，不再按密钥长度自动选；8002 验签只 pin `["HS512"]`。两侧都钉死，换密钥长度不会静默失配。历史坑：曾因 `.signWith(key)` 自动选 HS512、8002 硬编码 HS256 导致验签全挂。
  - **预置伴侣禁建库**：`is_preset=1` 的伴侣不允许用户建 collection（403），否则私有库会进入全员检索范围破坏隔离；预置伴侣仅允许系统级知识。
  - CORS 由通配 `*` 收紧为 `CORS_ORIGINS`（默认 3001）。
  - **启动注意**：`start-all.ps1` 用 `Start-Process` 不继承当前 shell 环境，**必须先注入用户级变量再启动**（`[Environment]::SetEnvironmentVariable($n,$v,'Process')`），否则启动自检会按设计失败退出。
- **Java 密钥口径**：`application.yml` 的 `secret: ${JWT_SECRET:兜底值}` 中兜底值**仅限本地开发**，生产部署必须设置 `JWT_SECRET`（HS512 需 ≥64 字节）。本机已用 `setx` 设置用户级 `JWT_SECRET`，**必须用新终端重启** Java/8002 才生效。
- 登录转发（3001 前端用）走 `trust_env=False`，上游 Java 5xx 返回 502 而非伪装成 401 密码错误。
- 回归资产在 `tests/rag_regression/`（18 篇文档 / 26 条预期 / `run_regression.py`），判定口径见该目录 `README.md`。

### 接口约定

- 请求体 `ChatRequest`：`{ systemPrompt, messages[{role,content,images?}], userMessage, images?, userId?, companionId? }`（images 为 base64 data URL；companionId 用于 RAG 知识库路由）。
- 统一响应包装 `APIResponse`：`{ success, message, data, timestamp }`。
- SSE 流式格式：每行 `data: {"delta": "文本", "done": false}\n\n`，结束帧 `{"delta": "", "done": true}`；前端按 `data: ` 前缀逐行解析。
- 关键端点：`/api/v1/ai/chat/stream`（普通流式）、`/api/v1/ai/chat/langchain/stream`（RAG + Function Calling 增强流式）、`/api/v1/ai/suggestions`、`/api/v1/memory/{user_id}`、`/api/v1/mood/{user_id}`。
- **流式端点鉴权（P1-5 已完成）**：两个 `/stream` 端点用 `Depends(verify_service_token)` 校验 `X-Service-Token` 头，不匹配返回 401；`SERVICE_TOKEN` 未配置时跳过。**必须用依赖注入**——写在函数体内会被 Pydantic body 校验抢先（无 token + 非法 body 会返回 400 而非 401）。**仅防误调，非安全加固**：前端 token 会进浏览器产物。

### 前端结构

- 页面在 `frontend/src/pages/`，路由见 `src/router/index.ts`；`@` 别名指向 `src/`（`vite.config.ts`）。
- `ChatPage.vue` 是核心页面：`enableRAG` 开关（默认开启）决定调用 LangChain 流式端点还是普通端点；聊天状态在 `stores/chat.ts`，伴侣数据在 `stores/companion.ts`。
- **伴侣编辑只有一个入口**：`/create?edit={id}`（`CreatePage` 编辑模式）。`/settings/:id` 已改为**路由级 redirect** 到该地址，仅作老书签兜底；`SettingsPage.vue` 不再注册路由。聊天页齿轮与广场卡片菜单都直接跳 `/create?edit=`。**新增编辑能力请改 CreatePage，不要再复活 SettingsPage**。
- **业务缓存清理**：`lib/api.ts` 的 `BUSINESS_CACHE_KEYS` 列出所有本地副本 key（会话/目录/情绪/记忆/内容/待办/场景），`clearBusinessCache()` 供 `logout`、`forceLogout` 与个人页「清除本地缓存」共用。**清业务缓存不清 token**（个人页按钮依赖此语义）。`ai-notes` 已移除（笔记改存后端）。

### 笔记模块（Java，2026-11-16）

`/api/v1/notes` 四个端点（列表分页对象 / 新增 / 更新 / 删除），表 `note`（`user_id` + `companion_id` + `content` + `tags` 逗号分隔）。归属校验：他人笔记统一 400「笔记不存在」，不区分无权（防探测）。**删除伴侣时笔记与会话/消息同事务逻辑删除**。前端 `stores/note.ts` 已从 localStorage 迁到 API，`NotesPage.vue` 提供「写笔记」模态框。详见 `docs/任务十一-笔记后端实施方案.md`。聊天页草稿态守卫 toast（`saveMessageAsNote` 的「先发一条消息」分支）为防御性代码：草稿态没有消息操作条，UI 无触达路径（2026-11-17 笔记页验收结论，接受现状不修）。

## 配置

- `backend/.env`（已被 gitignore）：`ZHIPU_API_KEY`（文本/视觉/图像生成共用）、`ZHIPU_BASE_URL`、`ZHIPU_MODEL`（文本 `glm-4.5-air`）、`ZHIPU_VISION_MODEL`（视觉 `glm-4v-flash`）、`ZHIPU_IMAGE_MODEL`（图像 `cogview-4`，置空走 SVG 降级）、`LLM_TEMPERATURE`/`LLM_MAX_TOKENS`/`LLM_TOP_P`，另有 `DATABASE_URL`（SQLite 或 PostgreSQL）、`REDIS_URL`、`APP_HOST`/`APP_PORT`/`APP_DEBUG`、**`SERVICE_TOKEN`**（流式端点共享密钥，留空则不校验）。键名清单见 `backend/.env.example`。密钥只写 `.env`，文档一律 `sk-***` 占位。
- `frontend/.env.development`（已被 gitignore，**不入库**）：`VITE_API_BASE_URL`（8081）、`VITE_AI_BASE_URL`（5000）、`VITE_SERVICE_TOKEN`（与后端一致）。入库的是 `frontend/.env.example` 模板。**不要给 `.env.development` 加 `!` 反向例外**——加了 token 后就会泄漏进 git 历史。
- `AI_INTEGRATION.md` — 双链路架构文档，密钥一律 `sk-***` 占位（历史版本曾含明文，git 历史中仍存留旧智谱密码，勿再引用）。
- **Java 端密钥注入**：`backend-java/application.yml` 中 MySQL/Redis 密码为 `${MYSQL_PASSWORD:}` / `${REDIS_PASSWORD:}`，**JWT 签名密钥为 `${JWT_SECRET:开发默认值}`**——三者的模板见 `backend-java/.env.example`。本机已设用户级变量（`setx`）；**必须新开终端启动 Java 才生效**，连接失败先排查环境变量。Redis 装在 `D:\IDEA\Redis-x64-3.2.100`（3.2.100），以 Windows 服务「Redis」方式运行、开机自启，conf 设有 `requirepass`，连接失败先查 `REDIS_PASSWORD` 与服务状态。未设置 `JWT_SECRET` 时启动会打印告警（`JwtUtil` 的 `@PostConstruct`），生产部署必须注入。
- `.gitignore` 已忽略 `.env`、`chroma_db/`、`ai_companion.db`、`*.tmp`、`*.stackdump` 等运行时/密钥文件；`RAG-Knowledge-System/backend/storage/uploads/`、`backend-java/uploads/` 上传数据同样不入库。**四个 `.env.example` 模板（backend / frontend / RAG / backend-java）通过 `!` 例外入库，不要误删这些例外规则。**

## 文档

- `docs/后端技术文档.md` — 后端实现细节（数据库表结构、接口）
- `docs/03-API接口文档.md` — API 规范
- `docs/LANGCHAIN_MIGRATION_GUIDE.md` — LangChain 集成与 RAG 说明，但该文件为 GBK 编码，按 UTF-8 读取会乱码，需转码后再读
- `docs/前端技术文档.md`、`docs/AI聊天功能优化方案.md`、`docs/功能上线排期指南.md`

## 工作约定（所有任务通用，优先级高于个人习惯）

1. 动手前先出改动清单：任何写代码/写文档的操作之前，必须先列出「将要新建/修改/删除的文件 + 每个文件改什么」，等用户确认后再执行。例外：纯咨询、跑只读命令（grep/读文件）不需要确认。
2. 会话收尾写回文档：每次会话结束前，把本次新拍板的决策、修正的错误、新增的约束写回 docs/ 对应文件（优先级依据是 `docs/04-重构接后端收敛点清单.md`），并在汇报末尾列出写了哪些文件。不允许只停留在口头结论。
3. 文档与代码冲突时，以代码实际状态为准，并把差异当作一条待修正项报告给用户，不要照着错误文档继续做。
