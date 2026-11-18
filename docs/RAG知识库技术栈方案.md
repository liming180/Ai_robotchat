# RAG 知识库技术栈方案（Milvus 升级）

| 项 | 值 |
| --- | --- |
| 撰写日期 | 2026-11-17 |
| 状态 | 技术栈方案已拍板；2026-11-17 变更：新增独立管理前端（Vue 3，端口 3001），见「前端方案」章节 |
| 服务定位 | `RAG-Knowledge-System/backend/`，端口 **8002** |
| 关联文档 | `docs/01-项目架构设计文档.md`、`docs/03-API接口文档.md`、`AI_INTEGRATION.md`、`CLAUDE.md`（RAG 双路口径） |

---

## 1. 背景与目标

项目四个服务（前端 3000 / Python AI 5000 / Java 业务 8081 / RAG 知识库 8002）中，仅 RAG 知识库未完善。现状四点不足：

1. **向量质量差**：当前 embedding 为 `SimpleHashEmbeddings`（逐字符哈希计数，256 维），是无 API 依赖的临时占位实现，语义检索能力有限；
2. **向量库能力受限**：Chroma 为嵌入式单机库，无 RBAC、无运维界面、索引类型单一；
3. **无鉴权**：8002 全部接口可匿名读写；
4. **无前端页面**（2026-11-17 变更：补建独立管理前端，见「前端方案」章节；Swagger + Milvus WebUI 仍作辅助入口）。

本方案目标：**向量库切换 Milvus（Docker Standalone 2.6.x）＋ 接入正式 embedding/rerank 模型（按附件 user.yaml 走智谱）＋ 登录鉴权关联现有 ai 伴侣账号 ＋ 补建独立管理前端（3001）**，同时保持 Python AI 服务（5000）现有集成契约不变。

## 2. 现状盘点（2026-11-17 实测）

### 2.1 8002 接口现状

统一前缀 `/api/v1/kb`；统一响应 `{success, message, data, error, timestamp}`；另有 `GET /health`。

| 方法 + 路径 | 说明 | 迁移后处置 |
| --- | --- | --- |
| POST / GET /collections | 知识库创建 / 列表（keyword、companionId、分页） | 保留，加鉴权 |
| GET / PUT / DELETE /collections/{id} | 详情 / 更新 / 级联删除（文档＋切片＋向量） | 保留，加鉴权；删除目标由 Chroma 改 Milvus |
| POST /collections/{id}/documents/upload | 多文件上传（json/md/txt ≤20MB）异步入库 | 保留 |
| POST /collections/{id}/documents/manual | 手动知识录入 | 保留 |
| GET /collections/{id}/documents | 文档列表（含状态/进度） | 保留 |
| GET / PUT / POST reindex / DELETE /documents/{id} | 文档详情 / 编辑（仅 manual）/ 重索引 / 删除 | 保留 |
| POST /retrieve | `{query, companionId? 或 collectionIds?, topK?, scoreThreshold?}` → `{chunks[], elapsedMs, searchedCollections}` | **契约不变**（5000 唯一依赖），加服务间鉴权 |
| GET /tasks/{taskId} | 异步任务进度（查 kb_document.task_id） | 保留 |
| GET /companions | 只读主库 companion 表，角色下拉 | 保留，加鉴权 |

### 2.2 数据与依赖现状

- **元数据**：MySQL `rag_knowledge` 库 3 表（`kb_collection` / `kb_document` / `kb_chunk`，均软删除）；另有一条**只读连接**连主库 `ai_companion`（companions 下拉用）——归属校验直接复用它。
- **向量**：每知识库一个 Chroma collection（`kb_{collection_id}`），cosine，256 维哈希向量。
- **存量极小**：`storage/chroma_db/` 约 0.4MB、2 个 collection、1 个上传文档 → **全量重导代价可忽略，不做数据迁移**。
- **文档解析**：仅 json / md / txt，`BackgroundTasks` 异步入库，进度挂 `kb_document.task_id`。
- **5000 依赖面**：仅 `POST /api/v1/kb/retrieve`，payload `{companionId, query, topK:4}`，超时 `RAG_TIMEOUT`（默认 3s）；超时/连接异常/5xx/4xx 回落本地 RAGStore（`backend/app/ai/rag.py`），空 chunks 是正常业务结果不回落。
- **边界（重要）**：5000 侧本地 RAGStore 除知识兜底外，还承载**用户记忆向量**（`add_memory` / `delete_memory`）。**本方案不迁移记忆向量**，该链路保持现状，是否迁 Milvus 列为后续可选项。

## 3. 选型决策

### 3.1 部署形态：Docker Milvus Standalone（排除 milvus-lite）

| 维度 | milvus-lite | Docker Standalone（✅ 选定） |
| --- | --- | --- |
| Windows 支持 | ❌ 官方仅支持 Ubuntu ≥ 20.04、macOS ≥ 11.0 | ✅ 本机 Docker 29.9.2 + Compose v5.6.1 + WSL2 后端就绪 |
| 索引类型 | 仅 FLAT | HNSW 等全量 |
| 分区 / Partition Key | ❌ | ✅（按伴侣隔离依赖它） |
| 用户/角色（RBAC） | ❌ | ✅ |
| 服务端 Function（embedding/rerank） | 不能满足本方案 | ✅ Milvus 2.6.x 支持 |
| 定位 | 原型 / 笔记本 | 单机生产形态 |

**结论：Docker Milvus Standalone 2.6.x（milvus + etcd + minio 三容器 Compose）。** 依据：

- milvus-lite 官方明确不支持 Windows，本机是 Windows 开发机，直接排除；即便借 WSL2 安装，lite 仅 FLAT 索引、无分区、无用户/角色，仍不满足需求（[Milvus Lite 官方文档](https://milvus.io/docs/milvus_lite.md)）。
- 附件 `user.yaml` 的 `credential` / `function`（textEmbedding / rerank providers）配置是 **Milvus 2.6.x「嵌入函数 + 配置文件凭据」机制**：凭据写入 milvus.yaml，由 Milvus 服务端在内部调用模型服务（[嵌入函数概述](https://milvus.io/docs/zh/embedding-function-overview.md)、[OpenAI 兼容 Provider](https://milvus.io/docs/zh/openai.md)）→ **Milvus 版本锁定 2.6.x**。
- 端口已实测空闲（2026-11-17）：19530 / 9091 / 2379 / 9000 / 9001 均无占用，零冲突。

### 3.2 向量模型与 Rerank（按附件 user.yaml）

user.yaml 定义并入 Milvus 配置文件 `milvus.yaml` 的 `credential` / `function` 段：

- **textEmbedding**：provider `openai`（智谱接口兼容 OpenAI 协议）→ `https://open.bigmodel.cn/api/paas/v4`，凭证 `zhipu_apikey` → 实际模型 **Embedding-3，2048 维**（默认；可选 256/512/1024/2048，本项目取默认，见 [Embedding-3 官方文档](https://docs.bigmodel.cn/cn/guide/models/embedding/embedding-3)）。
- **rerank**：provider `jina`（智谱 rerank 接口与 Jina/Cohere 契约兼容）→ `https://open.bigmodel.cn/api/paas/v4/rerank`，同一凭证（rerank 模型名以智谱官方文档为准，实施时核对）。
- **凭证管理**：与 `backend/.env` 的 `ZHIPU_API_KEY` 为同一密钥；`milvus.yaml` 落明文但**不入 git**，仓库内只留 `milvus.yaml.example` 模板（密钥一律 `sk-***` 占位），沿用项目密钥口径。

**检索链路（双路召回 + 精排，全部在 Milvus 内完成）**：

```
query ─┬─ 稠密召回：TEXT_EMBEDDING Function（Embedding-3, 2048 维）→ HNSW ANN
       └─ 稀疏召回：BM25 全文检索（Milvus 内置，text 字段配中文分析器）
                  ↓
        RERANK Function（provider jina → 智谱 rerank）精排
                  ↓
        topK chunks（含相似度得分，8002 侧按 scoreThreshold 过滤）
```

- **联调预案**：若 Milvus RERANK Function 与智谱 rerank 对接在实施时受阻，**降级为 RRF / WeightedRanker 融合排序**，8002 对外契约不变，不影响集成方。
- **成本注意**：向量在入库与查询时由 Milvus 内部调用智谱 API 产生计费调用（旧哈希方案为零调用），入库批量化可控制频次。

### 3.3 元数据存储：MySQL 保留

`rag_knowledge` 库 3 表结构基本不动：

- `kb_collection` 现有不可变字段 `embedding_model / dim / backend` 恰好记录新取值：`embedding-3 / 2048 / milvus`；
- `kb_chunk.vector_id`（`{document_id}::chunk_{index}`）继续作为 Milvus 侧业务主键，精确删除语义与现 Chroma metadata 删除一致。

### 3.4 Python 依赖变化（仅 8002）

| 动作 | 依赖 | 说明 |
| --- | --- | --- |
| 新增 | `pymilvus>=2.6` | 连接 Milvus |
| 新增 | `PyJWT` | 校验 Java 签发的 HS256 JWT |
| 移除 | `chromadb`、`langchain-chroma` | 知识向量不再落 Chroma |
| 不动 | 5000 侧 chroma 依赖 | 用户记忆向量链路保持现状（另一服务） |

## 4. 总体架构

```
前端 3000 ── 登录(Java) 拿 accessToken ──┐
                                        │ Bearer JWT
Java 8081 ── 签发/校验 JWT (JWT_SECRET) ─┼──→ RAG 8002（管理接口：知识库/文档/任务/companions）
                                        │        │ 元数据 → MySQL rag_knowledge
                                        │        └─ 向量 → Milvus 19530（etcd 2379 / minio 9000-9001）
Python 5000 ──── POST /api/v1/kb/retrieve（X-Service-Token）──→ 8002
    │                                                └─ Milvus hybrid_search + RERANK
    └─ 超时/异常 → 回落本地 RAGStore（记忆向量 + 兜底知识，现状保留）
```

**入库流**：上传/手动知识 → 解析（json/md/txt）→ 切片（langchain-text-splitters）→ 写 MySQL（kb_document/kb_chunk）→ `insert` Milvus（**只传文本**，dense 向量由 Milvus 服务端 Function 调智谱生成）。

**检索流**：5000 `search_knowledge` → `POST /api/v1/kb/retrieve`（带 X-Service-Token）→ Milvus 双路召回 + RERANK 精排 → 返回 chunks（字段与现状一致）。

## 5. Milvus 数据设计（示意，实施时按 2.6 官方文档核对参数名）

单集合 `kb_chunks` + Partition Key 按伴侣隔离：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INT64，auto_id 主键 | Milvus 内部主键 |
| text | VARCHAR（max_length 65535） | 切片原文，**配中文分析器**（BM25 用） |
| dense | FLOAT_VECTOR，dim=2048 | 由 TEXT_EMBEDDING Function 从 text 生成，插入时无需传 |
| sparse | SPARSE_FLOAT_VECTOR | 由 BM25 Function 生成 |
| companion_id | INT64，Partition Key | 按伴侣隔离与过滤 |
| collection_id / document_id | INT64 | 对应 MySQL 表主键 |
| chunk_index | INT32 | 切片序号 |
| vector_id | VARCHAR | `{document_id}::chunk_{index}`，精确删除定位 |

- **Functions**：`text_embedding`（TEXT_EMBEDDING，provider openai，embedding-3）、`bm25`（全文检索）、`rerank`（RERANK，provider jina → 智谱）。
- **索引**：dense → HNSW + COSINE；sparse → SPARSE_INVERTED_INDEX（BM25）。
- **检索**：hybrid_search 双路 → RERANK Function → limit topK（受阻降级 RRF，见 §3.2）。
- **隔离**：Partition Key 使每伴侣数据物理分片，检索自动路由，无需多 collection。

## 6. 鉴权设计（需求 4：登录账号关联现有 ai 伴侣账号）

原则：**不新建用户体系**，RAG 只做「验签 + 归属校验」。

- **Java 侧事实**（已实读源码）：`/api/v1/auth/login`（邮箱 + BCrypt 密码）签发 HS256 JWT——access 2h / refresh 7d，claims = `{userId, email}`，密钥 `JWT_SECRET`（环境变量注入，未设置时启动告警）；`SecurityConfig` 无状态，`/api/v1/auth/**` 放行。
- **RAG 侧**：共享同一 `JWT_SECRET` 环境变量（写入 8002 `.env`，不入库），PyJWT 验签取 `userId/email`；过期/无效 → 401。
- **登录用法（无前端页面下的两种方式）**：
  1. **主应用登录复用（主路径）**：在主前端（3000）登录得到的 accessToken，直接以 `Authorization: Bearer <token>` 调 8002 管理接口——账号即 ai 伴侣账号，零新增登录动作；
  2. **转发登录（调试增强）**：8002 新增 `POST /api/v1/auth/login`，原样转发 Java 8081 并回传 token，便于 Swagger / Postman 独立调试（不碰邮箱验证码链路）。
- **归属校验**：管理接口校验资源归属（companion 属主 = JWT 中的 userId，经现有只读主库连接查 companion 表）；他人资源统一按 403/400 处理，与主后端「防探测」口径一致。
- **服务间调用**：5000 → 8002 检索带 `X-Service-Token`（复用 5000 流式端点现有 `SERVICE_TOKEN` 共享密钥机制，8002 同名环境变量），缺失/不匹配 → 401。

**鉴权矩阵**：

| 接口 | 鉴权方式 | 校验 |
| --- | --- | --- |
| POST /api/v1/auth/login（新增，转发） | 无需 token | 转发 8081 |
| GET /health | 开放 | — |
| /api/v1/kb/retrieve | `X-Service-Token` | 服务间共享密钥 |
| collections / documents / tasks / companions 全部管理接口 | `Authorization: Bearer JWT` | 验签 + companion 归属 |

## 前端方案（2026-11-17 变更新增）

**结论：后端零新增框架**。FastAPI 保持纯 API 服务；前端为独立 Vue 3 应用，生产打包后可选由 FastAPI `StaticFiles` 一行挂载托管静态产物（可选项，非框架依赖）。

| 项 | 决策 |
| --- | --- |
| 目录 | `RAG-Knowledge-System/frontend/` |
| 技术栈 | Vue 3.4 + TypeScript + Vite 5 + Pinia + vue-router + Tailwind CSS 3.4 + element-plus（与主项目 `frontend/` 完全同栈，版本对齐） |
| 端口 | 开发 **3001**（3000 被主前端占用，已实测空闲）；API 地址 `http://localhost:8002`（`VITE_RAG_API_BASE_URL`） |
| 页面 | 登录 / 知识库列表 / 知识库详情（文档+上传+任务进度）/ 检索调试 |
| 登录 | 登录页 → 8002 `POST /api/v1/auth/login`（转发 Java 8081）→ accessToken 存 localStorage，后续请求带 `Authorization: Bearer` |
| 后端配套 | `main.py` 挂 CORSMiddleware 放行 3001（`CORS_ORIGINS` 配置）；新增 `app/api/v1/auth.py` 转发登录；JWT 鉴权强制化仍在 Phase 2 |
| gitignore | 补 `!RAG-Knowledge-System/frontend/.env.example` 与 `!RAG-Knowledge-System/frontend/src/lib/` 两条例外（`*.env` / `lib/` 规则会误伤，主前端有同款先例） |

---

## 7. 接口契约（对 5000 的影响面）

| 项 | 结论 |
| --- | --- |
| `/api/v1/kb/retrieve` 请求/响应结构 | **完全不变**（`{companionId, query, topK}` → `{chunks[], elapsedMs, searchedCollections}`） |
| 5000 侧改动 | 仅一处：`backend/app/ai/langchain_client.py` 调用时增加 `X-Service-Token` 请求头 |
| 8002 侧新增 | `POST /api/v1/auth/login` 转发接口；其余路径不变 |
| 统一响应包装 | `{success, message, data, error, timestamp}` 不变 |
| 工具选择规则 | 不受影响：本人记忆 → `search_user_memory`；伴侣设定 → `search_knowledge`（改后双向回归，见 §10） |

## 8. 功能清单（用户需求 → 方案落点）

| # | 需求 | 落点 |
| --- | --- | --- |
| 1 | RAG 知识库前端页面 | **2026-11-17 变更：已纳入**——独立 Vue 3 应用 `RAG-Knowledge-System/frontend/`（端口 3001），登录/知识库/文档/检索四页；Swagger 与 Milvus WebUI 保留为辅助入口 |
| 2 | 向量库用 Milvus，确定 lite 还是 docker | **Docker Standalone 2.6.x**（§3.1，Windows 下 lite 不可用且能力不足） |
| 3 | user.yaml 定义的 rerank / textEmbedding 模型 | Embedding-3（2048 维）+ 智谱 rerank，经 Milvus 2.6 Function 机制在服务端调用（§3.2） |
| 4 | 登录账号关联现有 ai 伴侣账号 | 共享 `JWT_SECRET` 验签 + 转发登录接口（§6） |
| 5 | 功能参考当前项目所需 | 知识库按伴侣隔离 CRUD、文档上传/手动知识/异步入库/任务进度、兼容 5000 的检索（双路+精排）、鉴权、数据重导（§2.1、§8 表） |

## 9. 部署与端口规划

- **项目内新建 `deploy/milvus/`**：`docker-compose.yml`（milvus-standalone 2.6.x + etcd + minio）、`milvus.yaml`（并入附件 user.yaml 内容，含明文密钥，**加入 .gitignore**）、`milvus.yaml.example`（占位模板，入库）；`D:\网站UI设计\资料\deploy\milvus\user.yaml` 作为配置母本。
- **端口**（已实测空闲）：19530（gRPC）/ 9091（metrics + WebUI）/ 2379（etcd）/ 9000、9001（MinIO）；Attu 可选（默认 8000，部署前确认空闲）。现有 3000/3306/5000/6379/8002/8081 不受影响。
- **Milvus 自身鉴权**：开启 `authorizationEnabled`（RBAC），创建专用业务账号（如 `milvus_rag`），8002 以 token 连接，凭据入 8002 `.env`（不入库）。
- **数据卷**：Milvus/etcd/minio 各自挂 Docker volume，持久化重启不丢。
- **常驻方式**：Docker Desktop 建议开机自启（与 Redis Windows 服务化口径一致）；`scripts/start-all.ps1` / `stop-all.ps1` 增加 milvus `docker compose up -d` / 停止与健康检查（Phase 4 改造项）。

## 10. 迁移与重导

旧 256 维哈希向量与新实现（2048 维 Embedding-3）**不兼容，不做迁移**；存量仅 0.4MB，直接重导：

1. 部署 Milvus（deploy/milvus + milvus.yaml 凭证配置）；
2. 建 `kb_chunks` 集合与索引；
3. 重建知识库记录（`embedding_model=embedding-3 / dim=2048 / backend=milvus`）→ 重新上传文档 / 手动知识（现存量：1 个 md + 少量手动知识）；
4. 8002 单服务回归：上传→切片→检索全链路；
5. 5000 加 `X-Service-Token` 后联调回归，重点用例：
   - **工具选择双向测试**（CLAUDE.md 口径）：本人记忆/聊天历史走 `search_user_memory`，伴侣设定走 `search_knowledge`，防止偏见翻侧；
   - **RAG 双路降级测试**：停 8002 → 5000 自动回落本地 RAGStore；8002 返回空 chunks 不回落；
   - 鉴权用例：无 token 401、他人 companion 403/400、服务间 token 错误 401。

## 11. 实施阶段拆分（后续编码任务建议）

| 阶段 | 内容 | 主要产物 |
| --- | --- | --- |
| Phase 1 | Milvus 部署 | `deploy/milvus/`（compose + milvus.yaml + example）、RBAC 账号、健康检查 |
| Phase 2 | 8002 改造 | MilvusStore 替换 ChromaStore、Function 接入（embedding/BM25/rerank）、JWT 鉴权 + login 转发、requirements 更新 |
| Phase 3 | 重导与单服务回归 | 重导脚本/操作记录、8002 全链路验证 |
| Phase 4 | 集成与回归 | 5000 加 header、start-all/stop-all 改造、双向工具测试、文档收口 |
| Phase 5 | RAG 管理前端（2026-11-17 新增） | `RAG-Knowledge-System/frontend/` Vue 3 应用（3001）、8002 CORS + 转发登录 |

> 每阶段动手前按工作约定先出「文件级改动清单」，确认后编码。

## 12. 风险与待确认项

1. **RERANK Function 对接**：Milvus 2.6 rerank 机制与智谱 rerank（Jina 兼容）的参数细节以官方文档为准，实施时核对；受阻则降级 RRF（契约不变）。
2. **智谱 rerank 模型名**：user.yaml 未写模型名，实施时按智谱官方文档确认。
3. **计费与延迟**：embedding/rerank 走智谱 API 为计费调用；检索链路新增一次 rerank 往返，`RAG_TIMEOUT`（3s）可能需上调（实施时压测定值）。
4. **中文 BM25 分析器**：需在 2.6 实测中文分词效果，不佳则弱化稀疏路权重（WeightedRanker）。
5. **密钥面扩大**：`JWT_SECRET`、Milvus 凭证、zhipu_apikey 三者新增到 8002/milvus 配置，全部走 `.env` / gitignore 文件，不入库。
6. **资源占用**：Milvus + etcd + minio 常驻内存约 2–4GB，Docker Desktop 需常驻；笔记本场景留意。
7. **后续可选项（本期不做）**：pdf/docx 文档格式扩展、用户记忆向量迁 Milvus；主前端集成知识库管理页（已有 RAG 独立前端 3001，优先级降低）。

## 13. 参考资料

- [Milvus Lite 官方文档（平台支持与限制）](https://milvus.io/docs/milvus_lite.md)
- [Milvus 2.6 嵌入函数概述（credential/function 配置机制）](https://milvus.io/docs/zh/embedding-function-overview.md)
- [Milvus OpenAI 兼容 Provider](https://milvus.io/docs/zh/openai.md)
- [智谱 Embedding-3（维度选项）](https://docs.bigmodel.cn/cn/guide/models/embedding/embedding-3)
- 智谱文本嵌入 API（/embeddings，Embedding-3 默认 2048 维）：docs.bigmodel.cn
- 项目内：`CLAUDE.md`（RAG 双路与端口口径）、`docs/03-API接口文档.md`、`docs/04-重构接后端收敛点清单.md`
