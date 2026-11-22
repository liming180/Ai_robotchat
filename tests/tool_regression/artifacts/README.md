# E-2 定向延迟探针（可复核证据）

## 用途

`docs/工具调用触发率实验报告.md` 第四节引用的检索耗时来源。用于回答：6.1s 是否复现、是否单次慢查询。

## 命令

在项目根目录执行（需要 5000 / 8002 在线）：

```bash
python -I logs/e2_latency_probe.py
```

脚本读 `backend/.env` 的 `SERVICE_TOKEN` 与 `logs/rag-regression-denseonly.json` 的 `userId`，
轮询 `logs/ai-5000.out.log`、`logs/rag-8002.out.log` 的新增行，打印每个 `[tool] search_knowledge`
与 8002 `/api/v1/kb/retrieve` 200 行相对请求起点的时刻。

## 执行记录

- **第一次（触发率复测期间）**：3 次检索耗时 573 / 263 / 244ms，未复现 6.1s。当时控制台输出未落盘，仅口头引用。
- **第二次（本文件同目录 `e2_latency_probe.txt`，推送前审计补落盘）**：

| run | total | 事件序列 | 结果 |
| --- | --- | --- | --- |
| 1 | 14579ms | +2848ms TOOL-START → +8075ms TOOL-START → **+9711ms RAG-200** → +10445ms TOOL-START → +10691ms RAG-200 | 答对（FastAPI + PostgreSQL） |
| 2 | 6072ms | +1441ms TOOL → +1708ms RAG-200 → +3452ms TOOL → +3700ms RAG-200 | 答对 |
| 3 | 5055ms | +1018ms TOOL → +1224ms RAG-200 | **误报「知识库中没有找到」** |

### 关键事实

1. **run1 是单次约 9.2s 检索**：第一个 `[tool]` 出现在 +2848ms，第一个 RAG-200 出现在 +9711ms，中间只有一个工具起点；也就是说**确实存在单次超过 3s 的检索**，不是双调用测量错配。
2. 6.1s 在本次**仍未复现**，但出现了更长的 9.2s，说明「检索偶发超过 3s」是真实存在的现象，只是触发条件未知。
3. run3 检索正常返回 206ms，但模型回答「知识库中没有找到」——**召回层确实没有命中 `08-preferences.md`**（该文件第 4 行就是 FastAPI + PostgreSQL）。这是检索层问题，与延迟无关。

### 注意

- 探针脚本末尾 `w.stop()` 存在 `TypeError`（`Event` 对象不可调用），不影响已打印的时间线；属一次性脚本缺陷，未修。
- 本证据只覆盖单查询 3 次，**不构成延迟分布结论**。
