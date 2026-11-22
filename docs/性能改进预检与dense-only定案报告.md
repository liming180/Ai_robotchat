# 性能改进预检与 dense-only 定案报告

- 日期：2026-11-22
- 范围：RAG 检索链路配置定案（`RERANK_ENABLED`），不含工具调用触发率（单独立项）
- 前置报告：`docs/RAG聊天集成验收报告.md`（Phase 4）、`docs/BM25混合检索验收报告.md`、`docs/RAG知识库数据导入验收报告.md`

## 一、结论速览

| 项 | 结论 |
| --- | --- |
| 生产配置 | **采纳方案 c：`RERANK_ENABLED=false`（dense-only 免精排）**，已写入 `RAG-Knowledge-System/backend/.env` |
| 质量（测试口径 28 条） | 26/28；原始 26 条中 **25/26**，唯一 FAIL 为 `A-INTERFERENCE-01`（已知） |
| 质量（生产口径真实收益） | 从 **0/26 可用**（TEI 从未在 3s 内返回）提升到 25/26，并在触发检索时 **2/2 答对** |
| 性能 | 暖机后实测 751~2131ms，落进 3s 预算；**冷启动 16.4s 必然回落，长尾未量化**，见第六节 |
| 方案 b（小 reranker） | **搁置**，理由见第四节；TEI 代码与容器作为存量资产保留，一个开关可回 |
| 回滚 | 改 `RERANK_ENABLED=true` 并重启 8002，无代码改动 |

## 二、四方案决策矩阵

填格依据：dense-only 与 hybrid 两列为本机实测；a/b 列为量级推算 + 已知硬件事实。

| 方案 | 质量（测试口径 28 条） | 延迟 | 成本 | 判定 |
| --- | --- | --- | --- | --- |
| **a) GPU 跑 TEI** | 28/28（TEI 口径已实测 28/28） | 可进 3s | 需 GPU 机器 + 运维；本机无 GPU | 备选，暂不投入 |
| **b) 换小 reranker（bge-reranker-base 级）** | 预期接近 a，但未实测 | CPU 可达标（待压测） | 选型 + 压测 + 调参；增量价值见第四节 | **搁置** |
| **c) dense-only 免精排** | 26/28（原始 25/26） | 暖机 0.75~2.13s；冷启动 16.4s | **零**（只改开关） | **采纳** |
| d) hybrid + RRF 免精排 | 26/28（语义回退 2 条） | p50 0.23s | 质量未达启用标准，开关保持关闭 | 不采纳 |

- **a 与 b 的质量并未在 3s 预算下被证明优于 c**：TEI 口径 28/28 是 **测试态 `RAG_TIMEOUT=60`** 下测出的；生产 3s 口径下 TEI 实际是 0/26（详见第三节）。把 TEI 的质量当生产收益是口径错误。
- c 与 d 在 28 条上同为 26/28，但**失败的不是同一批**：c 失败 `A-INTERFERENCE-01`、`A-CONTRAST-02`（top1 是 `09-programming-guide`）；d 失败 `A-SEMANTIC-01/03`（BM25 噪声经 RRF 放大）。d 有额外运维面（双集合、双写、阈值尺度不同），在质量无优势时没有理由承担。

## 三、聊天层实测（生产口径，决定性数据）

方法：走 5000 真实端点 `/api/v1/ai/chat/langchain/stream`，用回归伴侣真实 `systemPrompt`，统计 5000 日志中 `[tool] search_knowledge` 增量判定是否触发（不靠答案内容猜）。

| 口径 | 样本 | 触发检索 | 触发后结果 |
| --- | --- | --- | --- |
| dense+TEI（现状） | 8 | **1/8** | 唯一触发的 `A-LONG-02` 在 3s 超时后回落，回答「没有找到」 |
| dense-only（方案 c） | 8 | **2/8** | **2/2 答对**：`A-LONG-01` 引用 `tenant:{tenantId}:course:{courseId}:v{version}` + 30 分钟原文；`A-INTERFERENCE-01` 答 FastAPI + PostgreSQL |

关键判断：

- `A-INTERFERENCE-01` 在 dense-only 下**不是「次优」而是正确**：检索层 top1 确实错位到 `09-programming-guide`，但**生产链路把 topK=4 的候选全部喂给模型**（`_search_knowledge_remote` 拼接全部 `content`），正确文档 `08-preferences.md` 在第 2 位（0.4233），模型据此作答正确。**检索层 FAIL ≠ 回答错误**，两者必须分层记录。
- TEI 口径的唯一触发用例超时回落 → 说明现状在生产上等于「知识库不可用」。c 是**从零到可用**，不是从 26/26 掉到 25/26。

## 四、为什么定案 c / 为什么搁置 b

**定案 c 的三条理由：**

1. c 严格优于现状：被触发时 2/2 答对且引用原文；TEI 现状下唯一触发用例超时答「没找到」。
2. 「放弃 TEI」不成立：`RERANK_ENABLED` 一个开关随时可回，TEI 代码、`deploy/milvus` 编排、容器全部保留；继续挂在 off 之外的状态只会让生产维持零收益。
3. 工具调用率与 c 正交且 c 是前置条件：若先修工具调用、检索仍 15s+ 超时，结果是「调用更多、回落更多」。必须先让被调用的检索按时返回。

**搁置 b 的理由：**

- dense-only 已落进预算，且触发后 2/2 答对；b 的收益是「把 top1 错位的那一两条拉回来」，但聊天层证明这类错位**已经被 topK=4 全量喂料吸收**，边际价值不足以支撑选型 + 压测 + 参数调优的完整成本。
- b 一旦引入，必须重新校准分数尺度（reranker 分与 COSINE 分不可混比），并重新实测全部 26 条——这与「零成本先拿到可用性」的目标方向相反。
- 触发条件（将来启动 b 的前提）：出现「检索层错位导致回答明显错误」的真实案例，或生产需要 top1 精准（如引用溯源、展示排序）。

## 五、本轮验证记录

1. **配置变更**：`backend/.env` 第 49 行 `RERANK_ENABLED=true → false`，`diff` 校验**仅此一行变化**。`config.py` 默认值本就是 `false`、`.env.example` 也是 `false`，故无代码改动。
2. **重启**：`stop-all.ps1 -Service 8002` → `start-all.ps1 -Service 8002`，`/health` 200。
3. **带 token 检索实测**（`A-INTERFERENCE-01` 同一查询）：

   | 次序 | 耗时 | `scoreScale` | top1 |
   | --- | --- | --- | --- |
   | 冷启动首次 | 16409ms | `cosine` | 0.4262 `09-programming-guide` |
   | 暖机 1 | 751ms | `cosine` | 0.4262 |
   | 暖机 2 | 851ms | `cosine` | 0.4262 |
   | 暖机 3 | 2131ms | `cosine` | 0.4262 |

   分数尺度已确认为 `cosine`，与 TEI 分、RRF 名次分**不可混比**（三套尺度分列记录）。
4. **28 条回归**（`--verify-only --mode dense`）：**26/28**。原始 26 条中 25 通过，唯一 FAIL `A-INTERFERENCE-01`（top1 `09-programming-guide`，期望 `08-preferences`）；新增 2 条对照 `A-CONTRAST-01` PASS、`A-CONTRAST-02` FAIL。`scoreScale` 自证全部为 `cosine`。
5. **对照用例聊天层补充实测**（本轮新增，避免报告留空白）：`A-CONTRAST-01`、`A-CONTRAST-02` 各跑 2 轮，**4/4 未触发 `search_knowledge`**，模型凭通用知识作答。也就是说这两条的失败属于「知识库根本没被查」，不是「查错了」。

## 六、本轮新增发现（须在后续任务中处理）

1. **topK=4 全量喂料是隐式容错机制**：聊天层的正确率并不依赖 top1。这既解释了 `A-INTERFERENCE-01` 答对，也意味着**回归判定若只看 top1，会系统性地低估生产可用性**（反之也掩盖 top1 质量问题）。判定口径应长期保持「检索层 / 聊天层」分层。
2. **`09-programming-guide.md` 是「万能干扰源」**：14 个 chunk，语义宽泛，在 dense-only 下两条 FAIL 的 top1 都是它。它是 dense 单路的结构性弱点，不是随机噪声——同一模式下可复现。
3. **冷启动会击穿 3s，但长尾分布尚未量化**：本轮实测 5 次检索，暖机后 751 / 851 / 2083 / 2131ms 均在 `RAG_TIMEOUT=3` 以内，但**重启后首个请求耗时 16409ms**（Milvus 服务端 embedding 函数建连），必然触发 5000 回落。暖机最慢一次 2131ms 已接近阈值上限，余量不足。**现有数据量（5 次）不足以给出 p95/p99，本报告不下长尾结论**；需单独立项用固定样本量量化分布后再定超时策略（预检预热 / 超时重试 / 提高 `RAG_TIMEOUT`）。**本报告不把 dense-only 包装成「延迟已彻底解决」。**
4. **工具调用触发率仍是第一瓶颈**：8 条样本 2/8 触发，且同用例轮次间触发与否随机，样本量不足以定论 → 已单独立项（≥20 条、3 次重复，产出触发率分布与随机性程度）。

## 七、环境终态

| 项 | 状态 |
| --- | --- |
| `RAG-Knowledge-System/backend/.env` | `RERANK_ENABLED=false`（唯一改动，仅本机 gitignored 文件） |
| 8002 | 已重启，`/health` 200，检索 `scoreScale=cosine` |
| 5000 / 8081 | 运行中（5000 `/health` 200；8081 `/health` 403 为鉴权预期，`/doc.html` 200） |
| Milvus | `kb_chunks` 47 行未动；`kb_chunks_hybrid` 47 行保留 |
| `HYBRID_SEARCH_ENABLED` | 仍 `false`，未开灰度 |
| TEI | 容器与代码保留，未删除、未停用 |
| 回归资产 | 新增 2 个 `-HYBRID` 伴侣/知识库保留；本轮未新建资产 |
| 凭据 | 全程未落盘；回归登录用内存传递，密码只读本地 `.rag_test_pw` |
| 临时脚本 | `logs/` 下（gitignored）：`contrast_chat_probe.py`、`regression-denseonly-rerun.txt`、`contrast-chat.txt` |

## 八、后续任务清单（不在本批范围）

1. 工具调用触发率实验与修法选型（进行中，单独立项）。
2. 检索长尾量化（p95/p99）与超时策略。
3. 3001 `RetrievePage.vue` 阈值提示：仅在 hybrid 将来启用时必须同步上线；本轮启用的是 dense-only，阈值语义仍为 COSINE，**暂无联动需求**。
4. 知识库无角色设定时禁止自称有设定（提示词约束）。
