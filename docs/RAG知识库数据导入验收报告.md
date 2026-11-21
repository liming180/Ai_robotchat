# RAG 知识库数据导入与检索验收报告

| 项 | 值 |
| --- | --- |
| 验收日期 | 2026-11-21 |
| 执行人 | Claude Code（自动化回归 + 人工排障） |
| 范围 | 任务清单未完成项 #1「数据导入与验收」 |
| 结论 | **功能验收 26/26 通过**；**性能项不通过**（单次检索 14–26s，远超 3s 预算） |
| 证据文件 | `logs/rag-regression-state.json`（原始 24/26）、`logs/rag-regression-state-final.json`（终版 26/26） |

---

## 1. 验收对象与环境

| 项 | 值 |
| --- | --- |
| 伴侣 A | `RAG回归-学习助手`（`48441a063805432efbe18c9a8a83c6b2`），知识域=编程/学习方法 |
| 伴侣 B | `RAG回归-生活管家`（`1711e2d17df495e74d01a75442ed4968`），知识域=饮食/居家/健康 |
| 知识库 | A `19d2aa86-8222-4a8f-9253-da2e6514b35c`（22 切片）、B `d96f255f-08dc-4b04-97f6-732f27d5b4f1`（25 切片） |
| 文档 | 18 篇（每伴侣 9 篇），经 8002 multipart 上传 → 切片 500/50 → Milvus Function 调智谱 embedding-3 → flush |
| 向量库 | Milvus v2.6.0 standalone，单集合 `kb_chunks`，Partition Key = `companion_id`(VARCHAR 36) |
| Rerank | TEI 自托管 `BAAI/bge-reranker-v2-m3`（CPU，float16），`RERANK_ENABLED=true` |
| 检索参数 | `topK=4`、`scoreThreshold=0`（与生产 5000 链路一致） |

---

## 2. 导入结果

| 伴侣 | 文档数 | 切片数 | 状态 |
| --- | --- | --- | --- |
| A 学习助手 | 9 | 22 | 全部 `completed` / `progress=100` |
| B 生活管家 | 9 | 25 | 全部 `completed` / `progress=100` |
| 合计 | 18 | **47** | 无失败、无 `errorMsg` |

**三路对账（2026-11-21 实测）**

| 数据源 | 总数 | 按知识库 |
| --- | --- | --- |
| MySQL `kb_chunk` | 47 | A=22 / B=25 |
| Milvus ORM（`Collection.query`） | 47 | A=22 / B=25 |
| MilvusClient（`client.query`） | 47 | A=22 / B=25 |

- `vector_id` 集合三路**完全一致**（MySQL == ORM == Client）。
- 两个伴侣的 `companion_id` 分区互相独立（2 个不同分区键）。
- 说明：`num_entities` 含已删除残留，本报告一律用双路 `query` 可见行数，不用 `num_entities`。

**切片规格偏差（如实记录）**

规格预期长文档约 7 个切片，实际 A 长文档 14 个、B 长文档 17 个。原因：`text_parser` 先按 Markdown 二级标题分节，再按 500 字切分，每节独立成片。内容无丢失，对账一致，但「约 7 片」的规格预期与实际不符，记为资产文档偏差，不为凑数改动已入库数据。

---

## 3. 26 条逐条对照

判定规则：正例要求 top1 为预期文档且含预定事实；禁止项按第 4 节口径；否定/隔离用例不把任意返回当命中。

| # | ID | 类型 | query | 预期文档 | top1 文档 | top1 分数 | 判定 | 重试 | 耗时ms |
|---|---|---|---|---|---|---|---|---|---|
| 1 | A-FACT-01 | fact | Python 虚拟环境固定使用哪个版本？ | 01-python-env.md | 01-python-env | 0.9790 | PASS | 是 | 19494 |
| 2 | A-FACT-02 | fact | hotfix/order-42 的并行工作区如何创建？ | 02-git-worktree.md | 02-git-worktree | 0.9896 | PASS | - | 16760 |
| 3 | A-FACT-03 | fact | 订单列表联合索引包含哪些列？ | 03-sql-index.md | 03-sql-index | 0.9898 | PASS | - | 21728 |
| 4 | A-SEMANTIC-01 | semantic | 怎样复习不容易忘？ | 04-spaced-repetition.md | 04-spaced-repetition | 0.0744 | PASS | - | 17920 |
| 5 | A-SEMANTIC-02 | semantic | 工作时总被消息打断怎么办？ | 05-focus-recovery.md | 05-focus-recovery | 0.8698 | PASS | - | 16911 |
| 6 | A-SEMANTIC-03 | semantic | 怎么避免同类问题反复踩坑？ | 06-error-journal.md | 06-error-journal | 0.1798 | PASS | - | 16691 |
| 7 | A-SEMANTIC-04 | semantic | 看完书却讲不明白，怎样检验理解？ | 07-reading-notes.md | 07-reading-notes | 0.9192 | PASS | - | 15038 |
| 8 | A-INTERFERENCE-01 | interference | 使用偏好里代码示例用什么框架和数据库？ | 08-preferences.md | 08-preferences | 0.0901 | PASS | - | 16805 |
| 9 | B-INTERFERENCE-01 | interference | 使用偏好里饭量和时间怎么记录？ | 08-preferences.md | 08-preferences | 0.2759 | PASS | - | 21184 |
| 10 | A-LONG-01 | long | 课程缓存键格式和过期时间是什么？ | 09-programming-guide.md | 09-programming-guide | 0.9825 | PASS | - | 25797 |
| 11 | A-LONG-02 | long | 测试环境每周什么时候发布？ | 09-programming-guide.md | 09-programming-guide | 0.9970 | PASS | - | 23583 |
| 12 | A-LONG-03 | long | 发布健康检查失败后怎么回滚？ | 09-programming-guide.md | 09-programming-guide | 0.9634 | PASS | - | 26026 |
| 13 | B-FACT-01 | fact | 北豆腐冷藏保存多久，温度多少？ | 01-ingredient-storage.md | 01-ingredient-storage | 0.9958 | PASS | - | 23110 |
| 14 | B-FACT-02 | fact | 本周两人的食材预算是多少？ | 02-weekly-budget.md | 02-weekly-budget | 0.9966 | PASS | - | 18547 |
| 15 | B-FACT-03 | fact | 两人份南瓜小米粥的小米、南瓜和水量是多少？ | 03-porridge-recipe.md | 03-porridge-recipe | 0.9992 | PASS | - | 21105 |
| 16 | B-SEMANTIC-01 | semantic | 叶菜洗完放不久就坏，怎么处置？ | 04-vegetable-storage.md | 04-vegetable-storage | 0.9871 | PASS | - | 23324 |
| 17 | B-SEMANTIC-02 | semantic | 躺下还很精神，睡前环境怎么调整？ | 05-evening-routine.md | 05-evening-routine | 0.9781 | PASS | - | 21500 |
| 18 | B-SEMANTIC-03 | semantic | 伏案久了肩颈紧，应该怎么调整？ | 06-desk-posture.md | 06-desk-posture | 0.9985 | PASS | - | 14228 |
| 19 | B-SEMANTIC-04 | semantic | 家里储备用品外观很像，怎么避免混用？ | 07-medicine-check.md | 07-medicine-check | 0.9928 | PASS | - | 17023 |
| 20 | B-LONG-01 | long | 鸡蛋和鲜牛奶应放冰箱门架吗？ | 09-life-handbook.md | 09-life-handbook | 0.9915 | PASS | - | 18774 |
| 21 | B-LONG-02 | long | 家庭牙科复诊通常安排在什么时候？ | 09-life-handbook.md | 09-life-handbook | 0.9912 | PASS | - | 17671 |
| 22 | B-LONG-03 | long | 家政上门是几点，临时改预约由谁处理？ | 09-life-handbook.md | 09-life-handbook | 0.9454 | PASS | - | 17034 |
| 23 | ISOLATION-A-01 | isolation | 南瓜小米粥具体怎么做？（A 问 B 的知识） | 不得命中 B 文档 | 09-programming-guide | 0.0001 | PASS | - | 15699 |
| 24 | ISOLATION-B-01 | isolation | FastAPI 和 PostgreSQL 的使用偏好是什么？（B 问 A 的知识） | 不得命中 A 文档 | 09-life-handbook | 0.0000 | PASS | - | 16773 |
| 25 | NEGATIVE-A-01 | negative | 公司火星基地电梯的备用密码是多少？ | 库中不存在 | 09-programming-guide | 0.0001 | PASS | - | 20970 |
| 26 | NEGATIVE-B-01 | negative | 南极科考站量子发动机怎么换滤芯？ | 库中不存在 | 09-life-handbook | 0.0000 | PASS | - | 18738 |

**合计**：26/26 PASS，总检索耗时 502.4 秒，单条 14.2–26.0 秒（均值 19.3 秒）。

**关键观察**

- 强信号正例（事实型、生活域语义型、长文档）top1 分数 0.87–0.999，区分度良好。
- 弱信号正例（`A-SEMANTIC-01` 0.0744、`A-SEMANTIC-03` 0.1798、`A-INTERFERENCE-01` 0.0901）分数低但** top1 文档正确且含预定事实**，属 rerank 对「语义相关但表述差异大」的诚实低分，不影响正确性。
- 隔离与否定用例 top1 均为 0.0000–0.0001，**无跨伴侣串数据**，无冒充命中。

**观察项（非缺陷，供后续定阈值参考）**

伴侣 A 的语义类 query top1 分数为 **0.07–0.28**（A-SEMANTIC-01 0.0744、A-SEMANTIC-03 0.1798、A-INTERFERENCE-01 0.0901），而伴侣 B 的语义类为 **0.98–0.99**，呈明显**双峰分布**。

- 提示：A 库文档与 query 的语义贴合度低于 B 库，可能源于 A 库文风更偏「技术手册式陈述」，B 库更偏「生活口语式描述」，与自然问句更接近。
- 风险：若把本次验收的「分数 ≥0.5」口径**推广为生产检索阈值**，A 库的语义类查询会被**误杀**（当前这些条目虽正确命中但分数仅 0.07–0.28）。
- 建议：生产阈值不要一刀切，先按伴侣分别观察分数分布（建议每伴侣累积 ≥50 条真实 query）再定；或采用「先按分数排序取 topK，再用阈值兜底」的两段式策略。
- 另注：本次验收的 0.5 只用于**判定禁止项是否被有效命中**，生产 `RETRIEVE_SCORE_THRESHOLD` 实际为 `0.0`，两者用途不同，未经确认不应互相套用。

---

## 4. 判定口径的明确化过程（重要，留痕）

**初始结果 24/26**（`logs/rag-regression-state.json`）：

| 用例 | 原始 FAIL 原因 | top1 分数 | 实际情况 |
| --- | --- | --- | --- |
| A-LONG-01 | 第 2 名命中禁止文档 `04-spaced-repetition.md` | 0.9825（正确文档，含事实） | 禁止项以 **0.0219** 低分同现 |
| NEGATIVE-B-01 | top1 命中禁止文档 `09-life-handbook.md` | 0.0000 | 4 项命中**全部 0.0 分**，排名仅为并列噪声 |

原始口径为「禁止文档出现在任意返回位置即失败」，暴露两个问题：
1. 正例中无关文档以 0.02 级噪声同现属正常检索行为，不应判失败；
2. 否定用例全 0.0 分时，位置序不代表置信度，按位置判定无意义。

**经用户确认后明确化的口径（2026-11-21）**：

> 禁止文档**分数 ≥ 0.5** 才算有效命中，**不按位置判定**。正例的位置风险由「top1 必须是预期文档」独立检查兜住。若禁止项以 ≥0.5 出现在任意位置，仍判 FAIL。

- 依据：实测正例 0.94–0.999、噪声 ≤0.03，分界清晰。
- 8002 生产默认 `RETRIEVE_SCORE_THRESHOLD=0.0`（未设下限），**本口径严于生产**。
- 明确化后的终版结果：**26/26**（`logs/rag-regression-state-final.json`）。

**如实声明**：通过率 26/26 是在验收过程中明确判定口径后得到的，**不是口径一开始就如此**。原始 24/26 记录、两条 FAIL 的完整命中明细、改判依据均保留在上述两个 state 文件中，可随时复核。同步已修正 `expected_results.json` 的 `scorePolicy` 与 `tests/rag_regression/README.md`，防止后续回归复现同样误判。

---

## 5. 本轮修复的缺陷

| # | 缺陷 | 证据 | 修复 |
| --- | --- | --- | --- |
| 1 | **API 全链路未接 Milvus**：上传/检索/删除仍调 Chroma | `ingest.py`/`retrieve.py`/`documents.py`/`collections.py` 硬编码 `get_chroma_store()`；Milvus 仅直连冒烟通过 | 全部改走 `get_vector_store()`；Chroma 实现原样保留为回退 |
| 2 | **Milvus 字段类型与业务 ID 不兼容**：`companion_id/collection_id/document_id` 为 INT64，业务是 UUID/preset 字符串 | schema 实测 `DataType.INT64` | 改 VARCHAR(36)，Partition Key 保留；重建空集合 |
| 3 | **统一接口缺配**：MilvusStore 缺 `add_chunks`/`delete_chunks`/`drop_collection(collection_id)`，检索返回结构不一致 | 与 ChromaStore 比对 | 补齐同名同参接口，返回 `(Document, score)` |
| 4 | **Milvus 不存文档标题**，检索结果 `documentTitle` 为空 | 首次 retrieve 返回 null | 检索后按 `document_id` 从 MySQL 批量补齐 |
| 5 | **登录转发继承环境代理**：8002→Java 被代理拦截，且 Java 5xx 被误报为 401 密码错误 | httpx 默认 `trust_env=True`；实测同机代理下 502 | `trust_env=False`；上游 5xx 保留 502，仅鉴权拒绝映射 401 |
| 6 | **`retrieve` 用 async def 包裹同步 pymilvus 调用**，慢检索阻塞事件循环 | 实测慢检索期间 `/health` 超时 15s 无响应；改同步后同场景 `/health` **200/3ms** | 改普通 `def`，由 FastAPI 线程池执行；契约与返回结构不变，可回滚 |
| 7 | 回归脚本结果只在结束时落盘，中途崩溃全丢 | 首轮崩溃后 `results=0` | 每条完成即写 state；单条两次超时记 FAIL 并继续 |

---

## 6. 性能项：不通过

| 指标 | 目标 | 实测 | 判定 |
| --- | --- | --- | --- |
| 单次检索端到端 | ≤3s（`RAG_TIMEOUT`） | **14.2–26.0s**（均值 19.3s） | **不通过** |
| 生产聊天链路可用性 | 3s 超时内完成 | 必然超时 → 5000 侧回落本地 RAGStore | **降级链生效但知识库实际不可用** |

### 根因（有代码与实测双证据）

1. **Milvus rerank deadline 源码硬编码 30 秒，不可配置**  
   `internal/util/function/rerank/model_function.go`：`base.callService(ctx, requestBody, 30)` → `context.WithTimeout(ctx, 30s)`。  
   `milvus.yaml` 无对应键，二进制 `strings` 扫描无命中，确认非配置项。

2. **CPU 推理是瓶颈，耗时近似线性 ≈24ms/字**（`bge-reranker-v2-m3`，float16，单容器 CPU）

| 候选条数 | 总字数 | TEI 总耗时 | 其中排队 | 其中推理 |
|---|---|---|---|---|
| 6 | 1382 | 33.6s | 8.1s | 16.8s |
| 4 | 944 | 22.7s | 6.2s | 8.8s |
| 2 | 515 | 11.1s | 2.9s | 5.5s |
| 1 | 295 | 6.6s | 0.6s | 6.3s |

3. **排除项**：TEI 日志显示请求均被接收并 `Success`，不是「没收到」；冷启动假说被推翻（预热 1.5s 后真实 4 候选仍 22–30s）。

4. **资源事实**：宿主 7.79GB，Docker VM 上限 3.718GB，TEI 常驻 2.2–2.35GB，Milvus ~0.28GB，宿主空闲 0.56–1.23GB。

### 临时措施（已实施，可回滚）

- 回归脚本 `topK` 固定 **4**，与生产 5000 `langchain_client.py` 的 `topK:4` 对齐（注释已写明原因与 30s 证据）。**不是降低标准，是与生产口径一致。**
- **未启用**「超时自动降 topK」：验收口径须固定，静默降级会污染对照表；仅保留单条重试 1 次并留痕。
- 实测降到 1 条仍需 6.6s，**缩放候选无法解决超时**。

### 改进建议（三选一，量化）

| 方案 | 措施 | 预期效果 | 成本/风险 |
|---|---|---|---|
| **A. 换更小 reranker** | 换 `bge-reranker-base`（~278M 参数，约为 v2-m3 的 1/2）或 `bge-reranker-v2-minicpm-layerwise` 轻量档 | 线性模型下推理约减半，4 候选 ≈11s；仍超 3s | 低（改 TEI `--model-id` 重建容器）；需重测精度，可能损失中文排序质量 |
| **B. 加内存** | Docker VM 上限 3.718GB → 8GB+，宿主加装至 16GB | 消除 swap 与排队；按实测排队占比 27%，预计 4 候选 22.7s→约 16s；**仍超 3s** | 中（硬件）；**单独加内存不足以达标** |
| **C. GPU** | 启用 CUDA 版 TEI + 独立显卡 | CPU→GPU 通常 10–30× 加速，4 候选可降至 **<1s**，满足 3s 预算 | 高（硬件+驱动+镜像 `:cuda-1.8`） |

**推荐路径**：短期先取方案 A 评估精度损耗；若仍不达标或精度不可接受，直接上方案 C。方案 B 仅作为缓解，不能单独达标。

---

## 7. 遗留与未完成

| 项 | 状态 |
| --- | --- |
| 鉴权强制化（JWT 验签 + 归属校验 + CORS 收紧 + retrieve 服务间 token） | 未开始（原清单 #2） |
| Phase 4 聊天集成验收（enableRAG 命中、停 8002 降级、工具选择双向回归） | 未开始（原清单 #3） |
| BM25 混合检索 | 未开始（原清单 #4） |
| 前端小补（手动知识编辑、创建库高级参数、状态筛选） | 未开始（原清单 #5） |
| Milvus root 改密、pymilvus ORM→MilvusClient、方案文档口径修正 | 未开始（原清单 #6） |
| 两个旧 Chroma 知识库去向 | 待用户拍板；Chroma 代码本阶段**未删除任何一行** |
| 长文档切片数（14/17 vs 规格约 7） | 记录为资产偏差，不改已入库数据 |

---

## 8. 回归资产

| 文件 | 用途 |
| --- | --- |
| `RAG-Knowledge-System/backend/tests/rag_regression/fixtures/{a,b}/*.md` | 18 篇测试文档（每伴侣 9 篇，四类功能点 + 干扰 + 长文档） |
| `.../expected_results.json` | 26 条预期（文档、事实标记、禁止项、`scorePolicy`） |
| `.../run_regression.py` | 真实 API 全链路：登录→建伴侣/知识库→上传→轮询→检索→判定 |
| `.../README.md` | 运行方式、密码通道、判定口径、30s deadline 说明 |

复跑命令（不重复导入）：

```powershell
cd D:\Ai_robotchat\RAG-Knowledge-System\backend
$env:RAG_TEST_EMAIL="<测试账号>"
D:\python\python.exe -I tests\rag_regression\run_regression.py --verify-only --state-file <state 文件>
```

密码来源优先级：`RAG_TEST_PASSWORD` → `D:\Ai_robotchat\logs\.rag_test_pw` → `getpass`。凭据全程不落盘、不打印、不写入本报告。
