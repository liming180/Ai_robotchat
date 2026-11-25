# RAG 知识库管理前端重构验收报告（2026-11-25）

> 目标：把 `RAG-Knowledge-System/frontend`（3001）从「只有列表 + 上传 + 检索三个裸页面」重构成一个能真正管理知识库的管理台，补齐后端已有但前端零入口的能力，并修掉会打断流程的缺陷。
> 范围：P0（修 bug）+ P1（补齐后端已有能力 + 布局重构 + 概览页）。P2（需改后端）只登记，不实施。

## 一、结论

| 项 | 结果 |
| --- | --- |
| 布局 | 左侧导航（概览 / 知识库 / 检索调试 + 8002 健康点）+ 顶部面包屑 + 内容区 `max-w-[1200px]` |
| 页面 | `/login`、`/overview`（新增）、`/collections`、`/collections/:id`、`/retrieve`，`/` 重定向到 `/overview`，未知路由兜底到 `/overview` |
| 新增文件 | 3 个 store、14 个组件、2 个工具库、1 个页面 |
| P0 缺陷 | 4 个已修（检索必 401 被踢下线、批量上传半成功误报、知识库下拉静默截断、删除后页码不回落） |
| P1 能力 | 8 项已补（文档详情+切片、手动知识编辑、状态筛选、切片参数、JSON 解析规则、启停、任务恢复、scoreScale 标注） |
| 量测 | `check_design` 在 1280×800 / 1440×900 / 1100×800 对 5 屏全部通过（0 问题） |
| 编译 | `npx vue-tsc --noEmit` exit 0；`npm run build` 成功（主 chunk 1142 kB / gzip 380 kB） |

## 二、P0：修掉的 4 个缺陷

### 1. 检索调试页必然 401，且会把人踢下线

- **现象**：`POST /api/v1/kb/retrieve` 挂的是 `verify_service_token`（`X-Service-Token`），前端从不带，实测返回 `{"message":"Invalid or missing X-Service-Token"}`。更糟的是 axios 拦截器对任何 401 都 `clearToken()` + 跳 `/login`，用户在检索页点一次「检索」就被登出。
- **修法**：`.env.development` 增加 `VITE_RAG_SERVICE_TOKEN`（与 `RAG-Knowledge-System/backend/.env` 的 `SERVICE_TOKEN` 同值），`lib/api.ts` 的 `retrieveConfig` 单独带该头、超时 90s；响应拦截器新增 `isServiceTokenFailure(message)`（正则 `/x-service-token/i`），命中时**只提示配置问题，不清凭证、不跳登录**。
- **验证**：检索页 401 时页面顶部显示「token 未配置或不一致」的明确文案；真检索返回 200。

### 2. 批量上传半成功被当成整体失败

- **现象**：`app/api/v1/documents.py:61-99` 在循环里逐个落盘 + 提交任务，任一文件非法就 `raise 400`，但此前的文件已入库。前端只报「上传失败」，用户重传 → 库里出现重复文档。
- **修法**：前端把校验提到提交前（`lib/uploadGuard.ts`：扩展名白名单 `json/md/txt`、≤20MB、空文件、无扩展名四类逐条拒绝并列出文件名），并对同一批里的重复文件去重。后端原子性未改，登记为 P2-1。

### 3. 知识库下拉静默截断

- **现象**：`GET /collections` 的 `pageSize` 上限是 100，旧检索页单次拉 100 条就当作全量，库多于此数时下拉缺项且无任何提示。
- **修法**：`api.listAllCollections()` 按 100 分页遍历直到取满（页数上限 50 兜底），`stores/collections.ts` 统一缓存，概览页与检索页共用。

### 4. 删除后页码不回落

- **现象**：在最后一页删掉最后一个库，页码停在已经不存在的页，页面空白。
- **修法**：`CollectionsPage` 在 `total` 变化后计算 `maxPage`，`query.page > maxPage` 时自动回退并重新拉取。

## 三、P1：补齐的能力（后端早就有，前端零入口）

| # | 能力 | 落点 | 说明 |
| --- | --- | --- | --- |
| 1 | 文档详情 + 切片预览 | `DocumentDrawer.vue` | `GET /documents/{id}?withChunks=true`，展示元信息、原始正文、切片列表（序号 / 字数 / vectorId / 复制） |
| 2 | 手动知识录入与编辑（F2.3） | `ManualDocDrawer.vue` | 新建走 `POST .../documents/manual`；编辑仅对 `source_type=manual` 开放，先拉 detail 取 `rawContent` 再 `PUT /documents/{id}`（后端会重建切片与向量） |
| 3 | 文档状态筛选 | `DocumentTable.vue` | 状态下拉 + 标题/文件名搜索 + 批量重索引 / 批量删除；失败原因并入标题格（单开列在 1280 下必被切） |
| 4 | 切片参数 | `CollectionFormDrawer.vue` | `chunkSize 50–2000`、`chunkOverlap 0–500`（校验重叠 < 长度），文案提示「只影响之后新入库的文档」 |
| 5 | JSON 解析规则 | 同上（高级折叠区） | `itemsPath / contentField / titleField / metaFields` 四项，全默认时不发送 `parserConfig`（传 `null`） |
| 6 | 知识库启停 | 列表页 + 编辑抽屉 | `PUT /collections/{id}` 的 `status: active|disabled`，停用后检索不再命中、数据保留 |
| 7 | 任务恢复 | `stores/tasks.ts` | 全局 2s 轮询；页面刷新后 `restoreFromDocuments(docs)` 按 `taskId` 继续跟踪未完成任务；单任务 403/断网只停该任务，不拖死整页 |
| 8 | 分数尺度标注 | 检索页 + 库内检索 | 读响应里的 `scoreScale`：`cosine` 显示百分比条与阈值；`rrf` 只显示数值，并提示「名次融合值 0.015–0.033，阈值被服务端忽略」 |

## 四、业务硬约束（本次新发现并写进前端）

**知识库必须绑定角色。** `app/vectorstore/milvus_store.py:478-479` 在 metadata 缺 `companion_id` 时直接 `raise ValueError("Milvus 入库必须提供非空 companion_id")`——Milvus 用它做 partition key。但 `POST /collections` 允许 `companionId` 为空，于是用户能建出一个「传什么文档都在向量化阶段失败」的空壳库。

前端处理：

- 新建/编辑抽屉把「绑定角色」设成必填（`prop="companionId"` + rules required + submit 前二次拦截），文案写明「向量库按角色分区：未绑定的库无法入库文档」。
- 详情页对历史上已存在的空角色库显示 `el-alert` 警告，指向「设置」补角色。

后端是否改为建库时强制 `companion_id`，登记为 P2-2。

## 五、验证

### 环境

- 8002 `/health` 200；8081 `doc.html` 200；3001 由 `npx vite --port 3001` 提供。
- 联调凭证：`VITE_DEV_TOKEN` 走 `seedDevCredentials()`（仅 `import.meta.env.DEV`），HS512 自签 JWT 存 `.env.development.local`（已被 root `.gitignore` 的 `*.env.*` 覆盖）。

### API 冒烟（真实库 + 真角色，跑完即删）

建库（`chunkSize 400` + 四项 `parserConfig`）→ `GET` 回读校验 → `PUT` 改名/改参数/停用 → 手动知识入库 completed 3 块 → `GET /documents/{id}?withChunks=true` 拿到 `rawContent` + 3 个 chunk（字段 `charCount/chunkIndex/collectionId/content/documentId/id/meta/vectorId`）→ `PUT` 编辑后重建完成 1 块 → `/retrieve` 命中 1 条、`scoreScale=cosine`、top1 0.4091、238ms → 删文档 + 删库清理。

### 量测（`check_design`）

| 屏 | 1280×800 | 1440×900 | 1100×800 |
| --- | --- | --- | --- |
| `/overview` | 通过 | 通过 | — |
| `/collections` | 通过 | 通过 | 通过 |
| `/collections/:id` | 通过 | 通过 | — |
| `/retrieve` | 通过 | 通过 | 通过 |
| `/login` | 通过 | 通过 | — |

修复过程中处理的具体问题：

1. `DocumentTable` 列宽总和超出容器（「更新时间」被切 27px、「失败原因」被切 137px）→ 删独立列 + 重排列宽，总宽压到 748px 以内。
2. `style.css` 的「珊瑚底配深字」规则错误命中 `plain` 变体，导致「录入知识」按钮 1.14:1 几乎隐形 → 规则限定 `:not(.is-plain):not(.is-text):not(.is-link)`，另给 `plain` 单独的亮字规则。
3. 面包屑链接点击区 39×20 → 加 `-mx-1 px-1.5 py-1`。
4. 深色底上 `text-neutral-500/600` 只有 4.13 / 2.45:1 → 在 `tailwind.config.js` 里**覆盖整套 `neutral`**，最暗底上也 ≥4.5:1。
5. 全仓 `text-[11px]`(49 处) / `text-[10px]`(1 处) → 统一 `text-[12px]`。
6. `el-input-number` 加减把手 32×15 → 检索页 topK 换 `el-select`（3/5/8/10/15/20/30），阈值换 `el-slider`。
7. `v-loading` 默认白色遮罩在深色卡片上留半圈灰环 → 改为深色蒙层 + 珊瑚色转圈。

### 联调踩到的两个环境坑（已修，写进 README）

1. **浏览器 Network Error 而 curl 正常**：8002 的 CORS 只放行 3001 两个 host，其它来源预检被 Starlette 400；叠加 uvicorn 只监听 IPv4 而浏览器先解析 `::1`。改为 Vite 同源代理 `/rag-api` → `http://127.0.0.1:8002`。
2. **Windows 上 Vite 被 EBUSY 打挂**：编辑器留下的 `.tailwind.config.js.<pid>.<uuid>.tmpdir/` 被 watcher 抓到 → `server.watch.ignored` 加 `**/*.tmpdir/**`、`**/.git/**`、`**/dist/**`。

### 环境侧发现（不属前端）

- **Milvus 停机时页面无感**：8002 的 `/health` 只探 MySQL，`milvus-standalone` Exited(1) 时左栏健康点仍是绿的，检索要重试 75 次后才报 UNAVAILABLE。本次 `docker compose up -d` 拉起后恢复。**冷启动首次检索 48.8s，暖机 238ms。**
- 检索超时文案已按这条写：「首次检索要等 Milvus 加载集合，冷启动可达 30–60s」。

## 六、P2 清单（需改后端，本次不做）

| # | 项 | 现状 | 建议 |
| --- | --- | --- | --- |
| P2-1 | 批量上传原子性 | 循环内 `raise 400`，之前文件已落盘 | 全批校验通过再落盘，或返回 `{accepted, rejected}` 的 207 语义 |
| P2-2 | 建库强制 `companion_id` | 后端允许空，Milvus 入库必失败 | `CollectionCreateRequest.companionId` 设 required，历史空库回填脚本 |
| P2-3 | `/health` 探 Milvus | **已由后端会话完成（2026-11-25）**：`probe_milvus` + 503；前端已跟三态健康点，见第八节 | ✅ 已闭环 |
| P2-4 | 集合列表分页上限 100 | 前端 `listAllCollections` 分页遍历绕过 | 后端放宽上限或提供 `/collections/stats` 聚合接口，省掉全量拉取 |
| P2-5 | 切片级编辑 / 删除 | 无 API，只能整篇重索引 | `DELETE /chunks/{id}` + `PUT /chunks/{id}`，用于修局部脏切片 |
| P2-6 | 文档列表服务端筛选 | 前端全量拉后本地过滤 | `GET .../documents` 补 `keyword` / `status` / 分页 |
| P2-7 | 任务列表接口 | 只能按 taskId 单查 | `GET /tasks?collectionId=&status=`，任务中心页才有数据基础 |
| P2-8 | 检索耗时归因 | 只给总 `elapsedMs` | 分阶段（embedding / search / rerank）返回，便于定位冷启动 |
| P2-9 | 预览 / 分块调参 | 无法试切 | `POST /documents/preview-chunks {content, chunkSize, chunkOverlap}` 返回预览块 |

> **2026-11-25 补充**：上表 P2 清单已升级为完整后端改造方案，见
> `docs/RAG后端改造方案.md`（11 项后端缺陷 + 5 项新能力，含逐条实测证据与改法），
> 可直接派给其它 agent 的提示词见 `docs/RAG后端改造派工提示词.md`。
> 其中原 P2-1（批量上传原子性）、P2-2（建库强制 companion）经实测确认是 **P0 数据/正确性缺陷**，
> 另有新发现的 **`/retrieve` 越权读取他人私有库 + 停用库仍可检索**（最严重）与
> `created_by=system` 生产库管理台不可见，一并升级为 P0/P1。

## 七、文件清单

新增：

```
src/components/layout/{AppSidebar,AppHeader,PageHeader}.vue
src/components/common/{StatCard,StatusTag,EmptyState,CopyButton}.vue
src/components/collection/CollectionFormDrawer.vue
src/components/document/{UploadPanel,DocumentTable,DocumentDrawer,ManualDocDrawer}.vue
src/components/retrieve/{RetrieveForm,RetrieveResultCard}.vue
src/pages/OverviewPage.vue
src/stores/{collections,tasks}.ts
src/lib/{format,uploadGuard}.ts
```

重写：`src/App.vue`、`src/router/index.ts`、`src/lib/api.ts`、`src/stores/auth.ts`、`src/pages/{CollectionsPage,CollectionDetailPage,RetrievePage,LoginPage}.vue`、`src/style.css`、`tailwind.config.js`、`vite.config.ts`（代理 + watch 忽略）、`.env.example`、`README.md`。
## 八、同日跟进：8002 `/health` 升级为 Milvus 真实探活（前端同步改造）

**背景**：另一会话在 2026-11-25 把 `RAG-Knowledge-System/backend/app/core/health.py` 的 `/health` 从「只探 MySQL」改成真实探活 Milvus（`MilvusClient.get_server_version()`、独立 2s 超时、1s 结果缓存），**向量库不可用时返回 HTTP 503**（`code=MILVUS_UNAVAILABLE`），`VECTOR_STORE_BACKEND=chroma` 或 `MILVUS_HEALTH_ENABLED=false` 时为 `disabled` 且仍是 200。此前前端只按「请求是否抛错」判断在线，会把「Milvus 挂了」误报成「8002 离线」，或更糟——照旧显示绿灯。

**前端改造**：

| 落点 | 改动 |
| --- | --- |
| `src/lib/api.ts` | `HealthInfo` 补 `vectorStore` / `milvus` / `milvusLatencyMs` / `milvusVersion`；新增 `HealthProbe { reachable, httpStatus, data, message }`；`health()` 不再走 `unwrap`，用 `validateStatus: () => true` 收下 503 并组装 probe |
| `src/stores/collections.ts` | `health: HealthProbe \| null`；getters `backendOnline`（进程可达）/ `vectorReady`（`milvus===connected\|disabled`）/ `milvusDown`（`unavailable`）；`healthChecking` 用于「检测中…」 |
| `src/components/layout/AppSidebar.vue` | 健康点四态：绿 `8002 在线 · <version>`、黄 `向量库不可用`、红 `8002 离线`、灰 `检测中…`；圆点包 `el-tooltip` 显示原因（含「请确认 milvus-standalone 容器在运行」） |

**当前实测**：`GET /health` 200，`vectorStore=milvus`、`milvus=connected`、`milvusLatencyMs=171`、`milvusVersion=2.6.0`，左栏渲染「8002 在线 · 0.1.0」绿灯。**503 黄点未做实机演练**：需要停 `milvus-standalone`，而同期另一会话正在做 Milvus 可用性收口，避免互相干扰；分支逻辑已由 `HealthProbe.httpStatus` 单点控制，后续可随时用 `docker compose stop milvus-standalone` 复演。

**同批视觉收口**：`src/style.css` 的 `.chip` 由 `px-2 py-0.5` 改为 `px-2 py-1` + `min-h-6`（检索页「试一试」三个示例 chip 实测 138×22，低于 24px 点击区下限）。`check_design` 复量 5 屏 × 2 尺寸，绿点/黄点文案与 chip 高度均通过（见第一节量测行的最近一次结果）。
