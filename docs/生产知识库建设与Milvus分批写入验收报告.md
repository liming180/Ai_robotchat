# 生产知识库建设与 Milvus 分批写入验收报告

| 项目 | 内容 |
| --- | --- |
| 日期 | 2026-11-24 |
| 状态 | **通过**（E-2 已于用户端到端复验后关账） |
| 关联 | `docs/诊断-前端聊天401根因与凭证配置点清单.md`、`docs/E-2检索召回修复验收报告.md`、`docs/04-重构接后端收敛点清单.md` P1-7 / P2-5 |

---

## 一、背景与根因

2026-11-24 端到端复验时，前端问小智（`preset-2`）「这个项目用的技术栈是什么来着？」返回「知识库里没有找到」。

诊断结论：
- 5000 确实调用了 8002 `/api/v1/kb/retrieve`（8002 日志 200）；
- `preset-2` 名下唯一的 active 知识库是 `a6ff8355`「小智的喜好（任务七验收）」，向量后端为 `simple-hash / 256 维 / hash`，**从未迁入 Milvus（0 向量）**，检索恒空；
- 28 条回归全绿的库绑定的是测试用户 `48441a06…`，不是预置伴侣——回归资产和生产路径是两条线。

## 二、决策

1. **回归资产与生产资产物理隔离**（用户拍板，已写入 CLAUDE.md 硬规矩）：回归夹具（`tests/rag_regression/fixtures` 的 a 九篇）继续留在回归库，维护操作（清理、reindex）不得波及生产库；反之生产库内容也不得作为回归基线。
2. **生产库只装真话**：验收标准是真实技术栈 **Vue3 + Spring Boot + FastAPI + MySQL**。E-2 原「FastAPI + PostgreSQL」标准作废——那是按 fixtures 的示例答案校准的，属于回归世界。
3. 人工事实块合法，但承担维护义务：项目技术栈变更时必须同步更新（已写入 CLAUDE.md）。

## 三、Milvus 单次 insert ≤64 缺陷修复

### 缺陷

Milvus 2.6.0 服务端硬限单次 insert 最多 64 条，超出返回 `code=1214 input数组最大不得超过64条`。原 `MilvusStore.insert()` 把整篇文档的切片一次 `collection.insert()`，**任何 >64 切片的文档都会入库失败**。历史回归文档最多 30 块，所以长期未暴露；生产建库导入第 1 篇（69 块）时第一次失败。

### 修复

`RAG-Knowledge-System/backend/app/vectorstore/milvus_store.py`：

```python
MAX_INSERT_BATCH = 64  # Milvus 服务端单次 insert 上限

for start in range(0, len(entities), MAX_INSERT_BATCH):
    window = entities[start : start + MAX_INSERT_BATCH]
    collection.insert(window)
collection.flush()  # 末窗统一 flush 一次
```

### 测试

- 新增 `RAG-Knowledge-System/backend/tests/test_milvus_batch_insert.py`（5 条，全部通过）：150 条 → 批次 `[64, 64, 22]` 且 flush=1；64 条单批；3 条单批；0 条不 insert 不 flush；常量值为 64。用假 collection 验证切窗逻辑，不依赖 Milvus 在线。
- `test_milvus_smoke` 全过。
- 回归库 28 条：**27/28**，`A-CONTRAST-02` 为既有失败，与修复前基线一致，无新增回退。

## 四、生产库建设

### 4.1 建库方式

预置伴侣禁止用户建库（`api/v1/collections.py` 的 `allow_preset=False`，403），生产库以 `created_by=system` 直接落库，等价于「系统级知识」，符合 `security.py` 的设计意图。

脚本：`RAG-Knowledge-System/backend/scripts/build_production_kb.py`（支持 `--dry-run` / `--apply`，包含独立 session 读取终态、MySQL/Milvus 切片数自检）。

### 4.2 最终库信息

| 字段 | 值 |
| --- | --- |
| collection_id | `3fcef9d1-658a-4348-aa50-cf81b501d483` |
| 名称 | 小智的项目知识库 |
| companion_id | `preset-2`（小智） |
| created_by | `system` |
| 向量后端 | milvus / embedding-3 / 2048 维 |
| documents | 6（5 篇文档 + 1 条人工事实块） |
| chunks | **338**（自检：MySQL=338，Milvus=338，一致） |

### 4.3 验收数字口径：621 → 338（决策，不是缩水）

用户要求在文档中如实记录本次口径变更。

- 初次按 10 篇文档导入：切片数 69/28/59/74/58/77/61/104/24/67 = **621**，加事实块 7 块，共 628 块。按当时口径「621 + 事实块」数字达标。
- **但检索实测不合格**：`AI聊天功能优化方案` 单篇 104 块，把「技术栈」类查询的 top-11 全部占满，人工事实块连 top-20 都进不去（与 E-2 同类的文档稀释问题）。一个答不出技术栈的知识库，即使块数达标也不满足关账要求。
- 因此将文档集收紧为 **5 篇描述现状的文档**（337 块）+ 1 条事实块 = **338 块**。剔除原因两类：
  1. **方案/排期/任务清单类**写的是「打算做什么」，不是现状，且长篇规划类文档会压垮检索；
  2. **验收报告类**引用 `tests/rag_regression/fixtures` 的虚构示例答案（FastAPI + PostgreSQL），导入会把回归世界的事实带进生产库。
- 结论：**621 是按块数校准的旧口径，338 是按检索可用性校准的新口径**。之后任何导入变更都必须同时满足「MySQL=Milvus 块数一致」与「真实问句能召回事实块」两个条件。

### 4.4 检索自检

查询「这个项目用的技术栈是什么来着？」，topK=8（`companionId=preset-2`）：

| 排名 | 分数 | 内容 |
| --- | --- | --- |
| 1 | 0.5420 | 01-项目架构设计文档（链接列表块） |
| 2 | **0.5374** | **本项目的技术栈（人工事实块）** |
| 3 | 0.5191 | 01 技术栈表格块 |
| 4 | 0.5170 | 01 架构图 |

排名 2、3 均含真实技术栈，足够模型作答。

## 五、端到端验收（用户复验通过）

- 我用 5000 真实 LangChain 流式路径 + `preset-2` 真实 `systemPrompt` 实跑：答案完整给出 Vue 3.4 / Spring Boot 3.1.5 / FastAPI / MySQL，并明确「不使用 PostgreSQL、Flask」。
- 8002 日志确认 `POST /api/v1/kb/retrieve 200`，5000 日志确认触发 `[tool] search_knowledge`。
- **用户前端复验通过，E-2 关账。**

## 六、清理与遗留

### 已清理

`a6ff8355`「小智的喜好（任务七验收）」：0 向量遗留库，长期 active 挂在 `preset-2` 检索路径上（出现在 `searchedCollections`）。已通过 `get_vector_store().drop_collection()` + `CollectionService.delete()` 逻辑删除，复核 `preset-2` 检索只返回生产库 `3fcef9d1`。

### 遗留（记入 docs/04 backlog，不阻塞关账）

1. **裸词召回不稳**：查询仅「技术栈」时事实块未进 top-8（01 表格进第 6）。完整问句正常。
2. **分隔符纯块噪音**：检索结果混入 4 条 `---` 纯分隔符块（0.5137/0.5135），不携带信息却占上下文。需在 `ingest.py` 切块后过滤纯分隔符/空白块，属 P2 清理项。
3. **P1-7 观察项**：Agent 改写 query 的检索形态覆盖未系统验证（同一问题不同改写下的召回稳定性）。

## 七、关账硬闸门（用户拍板，写入 CLAUDE.md）

**任何检索类修复关账前，必须有一条真实生产伴侣上的问答验证通过。** 做不到的，必须在验收报告显式标注生产伴侣数据状态，并补做验证后才算过。回归库全绿不等于生产可用——本次故障正是「回归 28 条全绿、生产伴侣 0 向量」的典型。
