# RAG 知识库管理前端（端口 3001）

Vue 3 + TypeScript + Vite 5 + Pinia + Tailwind CSS + element-plus（深色管理台），与主项目 `frontend/` 同栈。
面向 AI 伴侣的角色专属知识库：知识库 CRUD、文档上传 / 手动知识、任务进度、切片预览、检索调试。

## 启动

```bash
cd RAG-Knowledge-System/frontend
npm install
npm run dev        # http://localhost:3001
npm run build      # vue-tsc 类型检查 + 打包
npm run check      # 仅 TypeScript 类型检查
npm run lint       # ESLint（lint:fix 自动修复）
```

## 页面

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/login` | `LoginPage` | 账密登录，转发 8002 `/api/v1/auth/login` → Java 8081 |
| `/overview` | `OverviewPage` | 概览：知识库 / 文档 / 切片统计、按角色分布、最近更新 |
| `/collections` | `CollectionsPage` | 知识库列表：卡片 / 表格双视图、关键词与角色筛选、分页、启停 |
| `/collections/:id` | `CollectionDetailPage` | 详情：统计 + Tabs（文档 / 库内检索 / 设置） |
| `/retrieve` | `RetrievePage` | 检索调试：按角色或指定知识库召回，看分数尺度与切片 |

布局为左侧导航 + 顶部面包屑（`AppSidebar` / `AppHeader` / `PageHeader`）。

## 依赖服务

| 服务 | 地址 | 用途 |
| --- | --- | --- |
| RAG 后端 | http://127.0.0.1:8002 | 知识库 / 文档 / 切片 / 检索接口 |
| Java 业务后端 | http://localhost:8081 | 登录（8002 `/api/v1/auth/login` 转发，账号即主应用账号） |

## 配置

`.env.development`（不入库，模板为 `.env.example`）：

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `VITE_RAG_API_BASE_URL` | `/rag-api` | **走 Vite 同源代理**（见下），不要填 `http://localhost:3002` 之类的跨域地址 |
| `VITE_RAG_SERVICE_TOKEN` | 空 | `/retrieve` 的服务间密钥，必须与 `RAG-Knowledge-System/backend/.env` 的 `SERVICE_TOKEN` 同值 |
| `VITE_DEV_TOKEN` | 空 | **仅开发联调**：填一个 HS512 签发的 JWT，`main.ts` 的 `seedDevCredentials()` 会解出 `userId/email` 写入本地凭证，跳过登录页 |

改 `.env.*` 后必须重启 3001（Vite 构建期常量，热更新无效）。

### 为什么走 `/rag-api` 代理

浏览器直连 8002 会撞两件事：① 8002 的 `cors_origins` 只放行 `http://localhost:3001` 与 `http://127.0.0.1:3001`，其它来源的预检被 Starlette 直接 400；② uvicorn 只监听 IPv4，而浏览器会把 `localhost` 先解析成 `::1`。`vite.config.ts` 的 `server.proxy['/rag-api']` 把请求转发到 `http://127.0.0.1:8002` 并剥掉前缀，页面与 API 同源，浏览器不再发预检。

### 鉴权口径

- 管理接口（collections / documents / tasks / companions）用 `Authorization: Bearer <JWT>`，token 存 localStorage `rag_access_token`，401 清凭证回登录页。
- `/retrieve` 用 `X-Service-Token`，**与 JWT 是两套鉴权**。401 报文含 `X-Service-Token` 时只提示配置问题，**不清凭证、不跳登录**（否则用户在检索页点一次就被踢下线）。

## 与后端的硬约束

- **知识库必须绑定角色**：Milvus 以 `companion_id` 做 partition key，`app/vectorstore/milvus_store.py` 在 metadata 缺 `companion_id` 时抛 `ValueError: Milvus 入库必须提供非空 companion_id`。后端建库不拦空角色，前端把「绑定角色」设成必填，并在详情页对历史空角色库显示警告。
- **允许上传的扩展名**只有 `json / md / txt`，单文件 ≤ 20MB，前端 `lib/uploadGuard.ts` 提交前先校验，避免后端半成功留下脏数据。
- **预置伴侣（`preset-*`）不允许挂私有库**（后端 403），新建时下拉里直接禁用并标注。

## 已知未做（需后端配合）

见 `docs/RAG前端管理台重构验收报告.md` 的 P2 清单：批量上传的原子性、`/health` 探测 Milvus、集合列表分页上限、切片级编辑等。