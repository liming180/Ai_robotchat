# RAG 数据导入与检索回归资产

## 资产结构

- `fixtures/a/`：伴侣「RAG回归-学习助手」9 篇编程/学习文档。
- `fixtures/b/`：伴侣「RAG回归-生活管家」9 篇饮食/日程/健康文档。
- `expected_results.json`：26 条查询的预期文档、top1 事实标记、禁止命中项。
- `run_regression.py`：仅通过 Java / 8002 真实 API 创建数据、上传、轮询及检索。

两个长文档均超过 3000 个字符；各自缓存/冰箱、发布窗口/牙科复诊、回滚/预约改期三个事实点互相隔开。查询不是从正文机械复制标题，语义组重点考察非字面命中。

## 前置条件

1. Java 8081、RAG 8002、Milvus、TEI 在线；Milvus 集合使用 VARCHAR 业务 UUID。
2. 在 `RAG-Knowledge-System/backend` 目录执行，确保 `.env` 正确加载。
3. 测试账号只从进程环境读取，绝不写入代码、状态文件或报告。

```powershell
$env:RAG_TEST_EMAIL = '<测试账号邮箱>'
$env:RAG_TEST_PASSWORD = '<测试账号密码>'
# 状态文件放在 logs 等不入库目录；只含本次测试 ID、任务与实际命中，不含凭据。
D:\python\python.exe -I tests/rag_regression/run_regression.py --setup --state-file D:\Ai_robotchat\logs\rag-regression-state.json
```

再次只跑检索预期表：

```powershell
D:\python\python.exe -I tests/rag_regression/run_regression.py --verify-only --state-file D:\Ai_robotchat\logs\rag-regression-state.json
```

脚本创建前发现同名回归伴侣会停止，避免误操作已有数据。伴侣和知识库创建后立即写临时状态文件；发生中断时保留该文件供人工清理，不能盲目重复建库。

### 密码获取顺序

1. 环境变量 `RAG_TEST_PASSWORD`；
2. 本地文件 `D:\Ai_robotchat\logs\.rag_test_pw`（`utf-8-sig`，读后 `strip`；可用 `RAG_TEST_PW_FILE` 改路径）。文件由用户本地终端一次性创建，脚本只读不写、不打印内容；
3. 都没有时回退 `getpass` 盲打（需交互终端）。

### rerank 30 秒硬编码 deadline

- Milvus v2.6.0 的 rerank 模型调用 deadline 写在源码里：`internal/util/function/rerank/model_function.go` 的 `base.callService(ctx, requestBody, 30)`，**不是配置项**（`milvus.yaml` 无对应键，二进制 `strings` 扫描也无命中）。
- 实测（CPU、`bge-reranker-v2-m3`）：6 条候选约 33.6s（超时）；4 条约 22.7–23.9s；2 条约 11.1s；1 条约 6.6s。耗时近似线性 ≈24ms/字。
- 因此回归脚本固定 `topK=4`，与生产 5000 链路（`langchain_client.py` 的 `topK:4`）一致。**不做超时自动降 topK**：验收口径必须固定，静默降级会污染对照表；单条 rerank 超时仅重试 1 次（间隔 2s），且原始失败与重试结果都写入 state 与报告。

### 回归库归属（2026-11-21 鉴权强制化后）

两个回归知识库（`19d2aa86…` / `d96f255f…`）的 `created_by` 已一次性显式 UPDATE 为测试账号 `c4250e18…`，否则第二批鉴权上线后会 403 全挂。**第二批之后由脚本新建的库经 JWT 自动带 `created_by`，不再依赖手工补齐。**

### 本机代理与登录

- 8002 → Java 登录转发和本回归脚本都使用 `trust_env=False`，避免终端代理把 localhost 请求转成 502。
- 8002 只有在 Java 明确拒绝凭据时返回 401；Java 上游 5xx 现在映射为 502，不再伪装成密码错误。
- 已完成导入后只能执行 `--verify-only`，不得重复 `--setup`。脚本读取同一个 state 文件，不会重新上传或重切已有 47 个切片。
- 若交互式终端未继承 `RAG_TEST_PASSWORD`，脚本会用 `getpass` 请求一次不回显输入；密码不能出现在命令行、文件或日志中。

## 判定标准

- 每个伴侣 9 篇、总计 18 篇全部 `completed`、`progress=100`、`chunkCount>0`。
- 每篇通过 multipart 上传，禁止直写 Milvus；切片参数 500/50。
- 精确、语义、同构干扰和长文档用例要求 top1 是预期文档且包含预定事实。
- **禁止项判定口径（2026-11-21 验收中明确化）**：禁止文档分数 **≥ 0.5** 才算有效命中，**不按位置判定**。原因：否定/隔离用例常出现全部命中 0.0 的并列情形，此时排名只是噪声（`NEGATIVE-B-01` 实测四项全 0.0）。正例的位置风险由上方「top1 必须是预期文档」独立兜住。依据：实测正例 0.94~0.999、噪声 ≤0.03；生产 `retrieve_score_threshold` 默认 0.0，本口径严于生产。原始 24/26 的失败记录与改判依据见 `docs/RAG知识库数据导入验收报告.md`。
- 隔离用例要求另一伴侣的知识不出现在返回中。
- 否定用例**不得**把有返回当作命中，判定依据是**分数**而非返回条数：全部命中 < 0.5 即视为「无有效命中」，用例通过。
  - **已被实测证据满足（2026-11-21）**：`ISOLATION-A-01` 0.0001、`ISOLATION-B-01` 0.0000、`NEGATIVE-A-01` 0.0001、`NEGATIVE-B-01` 0.0000（四项全 0.0）。低分命中属 rerank 对无关内容的正确判定，不是「区分不开」。原始「未证明可区分前，不宣称负例通过」的保留条件已由上述实测数据解除。
- 开启 rerank 时 Milvus 返回的 `score` 是精排得分，不能与关闭 rerank 的 COSINE 分数直接比较。

## Chroma 保留约束

本阶段只接入统一后端开关，**不删除或改写 Chroma 实现**。Chroma 仍是独立回退后端。其删除是后续独立任务，必须同时满足：API 全链路回归全绿、用户决定两个旧库去向、Phase 4 聊天集成验收通过。
