# RAG 聊天集成验收报告（Phase 4）

- **日期**：2026-11-22
- **范围**：3000 前端 → 5000 Python AI → 8002 RAG → Milvus/TEI 全链路
- **口径**：功能通过与性能表现分开记，不混算通过率；性能问题单列。

## 一、结论摘要

| 维度 | 结论 |
| --- | --- |
| 聊天 RAG 功能链路 | **通过**：开关、路由、服务间鉴权、知识库检索、工具选择、三条降级路径均实测 |
| 检索性能 | **不通过**：生产口径 3s 超时必然触发；rerank 稳定在 9–54s，Milvus 30s 硬编码 deadline 仍是主瓶颈 |
| 环境复原 | **完成**：5000 回生产口径、`.env` 未改（SHA256 前 16 位 `fc720e95c8d9789e`）、8002 已重启、Milvus/TEI 在跑、四端健康 |

## 二、用例与结果

### P4-1 正常检索（功能模式）

**测试口径**：仅本次测试在 5000 进程环境设 `RAG_TIMEOUT=60`，**不改 `backend/.env`**。报告中的 60s 是测试专用值，禁止当作生产参数。

**请求**：伴侣 A（`48441a06…`），问"请查一下你的知识库文档，里面关于间隔重复是怎么安排复习的？请按文档内容回答。"

| 尝试 | 总耗时 | 8002 `/retrieve` | 5000 行为 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | 50s | 500（rerank deadline） | 回落本地，答案称无记录 | 失败 |
| 2 | 47s | 500（rerank deadline） | 回落本地，答案称无记录 | 失败 |
| 3 | 23s | **200** | 未回落，答案引用文档内容 | **通过** |

第 3 次答案包含 `04-spaced-repetition` 文档要点：对比实验、分散接触、检索难度、"每次复习先回忆、查漏补缺"等。工具日志确认 `[tool] search_knowledge query=间隔重复 复习安排`。

> 结论：**功能链路成立**（工具选择 → 带 `X-Service-Token` 调 8002 → Milvus 检索 → 答案落地）；**稳定性受性能拖累**，3 次中 2 次因 30s deadline 失败。

### P4-1P 生产口径降级

重启 5000，不注入 `RAG_TIMEOUT`（默认 3s），同一请求：

- 总耗时 **9s**
- 5000 日志：`[search_knowledge] 8002 RAG 服务异常，回落本地: ... Read timed out. (read timeout=3)`
- SSE 正常结束帧 `{"delta":"","done":true}`，客户端无 500/断流
- 答案允许为"没有找到"，**降级链成立**

### P4-2 8002 停机降级

- 停 8002 后同一请求：**9s**，日志 `NewConnectionError ... 由于目标计算机积极拒绝，无法连接`，SSE 正常结束
- 重启 8002（注入 `JWT_SECRET`）：`/health` 200，指纹仍为 `bf165acb`
- 恢复检索：首次 topK=4 在 44.6s 后 500（rerank deadline）；重试 topK=1 → 200/9.0s，topK=4 → 200/19.3s。**恢复确认成立**

### P4-3 空知识库

伴侣 `preset-1` 的知识库无切片：

- 直查 8002：200，`chunks=[]`，0.30s
- 聊天链路：4s，8002 返回 200 空结果，5000 **未触发本地回落**（回落日志计数 1→1），答案如实说"知识库里没有找到"

### P4-4 工具选择双向

| 用例 | 用户问题 | 新增工具日志 | 结果 |
| --- | --- | --- | --- |
| 用户记忆 | "我之前说过我喜欢什么？" | 仅 `[tool] search_user_memory ... keyword=喜欢` | **通过**，答案命中已有记忆"喜欢喝可乐" |
| 伴侣知识 | "你的性格设定是什么？" | 仅 `[tool] search_knowledge`（5 次不同改写） | **通过**（选择正确）；答案质量见观察项 |

### P4-5 前端开关

Playwright（系统 Edge，headless）注入登录 token，进入 `/chat/48441a06…`，拦截 `/api/v1/ai/chat/**` 返回最小 SSE：

- 初始 `aria-checked=true` → 请求 `http://localhost:5000/api/v1/ai/chat/langchain/stream`
- 点击开关后 `aria-checked=false` → 请求 `http://localhost:5000/api/v1/ai/chat/stream`
- 共 2 次请求，端点选择与 `useStreamingChat.ts` 逻辑一致，**通过**

### P4-6 启停脚本纳管 Milvus/TEI

- `stop-all.ps1 -Service docker`：exit 0，两个容器 Stopped，卷保留（`compose stop`，未 `down`）
- `start-all.ps1 -Service docker`：先 `compose up -d`，等 `milvus-standalone=healthy` 且 TEI `/health=200` 才放行，exit 0
- **首次实现 bug**：等待上限 180s，TEI CPU 冷启动实测约 3.5–4 分钟，脚本误判失败。已改为 600s，并每 15s 打印等待状态
- 第二次冷启动验证：约 4 分钟后就绪，exit 0；容器 Running/healthy，TEI health 200
- 容器已运行时重复执行：秒级通过，幂等

## 三、性能单列（不计入功能通过率）

| 场景 | 实测 |
| --- | --- |
| 8002 直查 topK=1 | 16.7s（首次）、9.0s、**54.0s** |
| 8002 直查 topK=2 | 10.1s |
| 8002 直查 topK=4 | 22.9s、24.3s、18.6s、19.3s、44.6s（500） |
| 5000 生产口径 | 3s ReadTimeout 必然触发，功能只能靠本地降级 |
| TEI 冷启动 | 约 3.5–4 分钟（CPU warmup） |

**根因未变**：Milvus v2.6.0 rerank deadline 源码硬编码 30s；CPU `bge-reranker-v2-m3` 约 24ms/字。候选数缩小仍不能稳定进入 3s。改进路径仍是更小 reranker / GPU；加内存只能缓解抖动。

## 四、观察项（非本阶段缺陷，需后续决策）

1. **P4-4b 幻觉风险**：知识库没有角色设定文档时，模型在 5 次检索后仍给出"睡前记录、喜欢散步"等具体习惯。工具选择正确，但答案把通用提示词内容与自造细节混在一起。建议后续在提示词或后处理中约束"检索无结果时不得自称有该设定"。
2. **8002 检索抖动大**：同样 topK=4，18.6–44.6s 波动，偶发 500；P4-1 三次尝试中两次失败。属于性能问题，不建议靠增加重试掩盖。
3. **5000 生产 3s 超时**与 8002 实际耗时差一个数量级，当前生产链路事实上的 RAG 能力等于"总是回落本地"。Phase 4 功能验收只能在测试态 `RAG_TIMEOUT=60` 下完成。

## 五、环境终态（现场复原）

| 项 | 终态 |
| --- | --- |
| 5000 | 生产口径（未注入 `RAG_TIMEOUT`，默认 3s）；`/health` 200 |
| 8002 | 已重启，指纹 `bf165acb`；`/health` 200，`mainDatabase=connected` |
| Java 8081 | `/doc.html` 200 |
| 前端 3000 | 200 |
| Milvus/TEI | 容器 Up，`milvus-standalone healthy`，TEI `/health` 200 |
| 正常检索 | topK=1 最终确认 200（54s，性能问题仍在） |
| `backend/.env` | 未修改，SHA256 前 16 位 `fc720e95c8d9789e` 与测试前一致 |
| 临时脚本 | `logs/phase4_p4_5.py` 已删除 |

**测试数据说明**：P4-5 前端实测在测试账号下新建了 1 个会话（标题以"开关测试"开头，创建时间 2026-11-22 13:14），未删除——删除属破坏性操作，等用户确认后处理。

## 六、本阶段代码改动

| 文件 | 改动 |
| --- | --- |
| `backend/app/ai/langchain_client.py` | `search_user_memory` / `search_knowledge` 入口打印 `[tool] ...`（`flush=True`），用于工具选择实测 |
| `scripts/start-all.ps1` | 纳管 `docker compose up -d`；等待 Milvus healthy + TEI health（600s）；修复 docker stderr 被 PowerShell 当终止错误；compose 日志改 UTF-8 落盘 |
| `scripts/stop-all.ps1` | 纳管 `docker compose stop`（保卷）；新增 `-Service docker` |
| `CLAUDE.md` / `docs/04-重构接后端收敛点清单.md` | 写回本报告结论与脚本口径 |

## 七、遗留

- 性能改进（GPU / 更小 reranker）仍是 Phase 4 功能可用的前置条件；当前只能降级运行。
- P4-4b 幻觉约束未修，建议单独立项。
- 本阶段改动尚未 commit（等用户确认报告后统一提交）。
