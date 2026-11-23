# request.systemPrompt 接入 Agent 验收报告

- 日期：2026-11-22（v5/v6 与构建成本补充：2026-11-23）
- 方案：方案 A（人设插槽），用户批准
- 状态：**v5 回退已修复，v6 全量通过；空值路径 general 补测 0/27 判定随机噪声；本批已 commit（`0573e33` + `375a7f6`），待推送前审计**
- 推送范围：两次 commit 去重后共 **11 个文件**（`0573e33` 11 个；`375a7f6` 8 个，其中 8 个与前者重叠）
- 前置：`docs/工具调用触发率实验报告.md`（该报告记录的实验口径是「systemPrompt 未接入」，本批已接通）

## 一、问题与结论

**问题**：前端建伴侣时保存的 `systemPrompt`（人设文本）从未到达模型。`langchain_client.py` 的 `_build_agent()` 固定调用 `build_system_prompt()`，`main.py` 的 `/api/v1/ai/chat/langchain[/stream]` 只传 `user_input / chat_history / personality / user_id / companion_id`。生产上所有伴侣实际都用平台默认提示词说话。

**结论**：本批把 `request.systemPrompt` 作为**插槽**接入 `build_system_prompt(person_section=...)`。结构约束全部达成，但**生产路径（非空 systemPrompt）的 persona 触发率未达标**：

| 约束 | 结果 | 证据 |
| --- | --- | --- |
| 非空 systemPrompt → L1 兜底句不出现，只有插槽 | ✅ | `test_person_section_suppresses_default_persona_sentence` |
| 空 systemPrompt → 输出与接入前**逐字一致**（含 L1 兜底句） | ✅ | `test_system_prompt_default_output_is_byte_identical`（真实 diff 黄金基线，非口头保证） |
| 插槽不得挤掉工具规则 1–8 与防编造规则 | ✅ | `test_person_section_keeps_tool_and_anti_fabrication_rules` |
| 接入不引入触发率回归（空串路径） | ✅ | v4 vs v3：fact 24/24、general 0/9，分类结论零变化 |
| 伴侣人设与工具规则冲突时工具规则优先 | ✅ | 冲突探针 3/3 仍调 `search_knowledge`，答案命中原文要点（字段名 camelCase 化） |
| **生产路径（小智插槽）persona 不退化** | **✅ v6 9/9**（v5 曾 8/9，已修复） | v6 全量复测；修复项见第九节 |

`pytest tests` **25/25 通过**（新增 4 条结构测试 + 1 条 v5 修复回归测试）。

## 二、实现

### 1. `backend/app/ai/prompts.py`

`build_system_prompt()` 新增 `person_section: str = ""` 参数，生成顺序：

```
{人设层}【角色设定】
{companion.systemPrompt}
（以上仅定义身份与说话风格；若与下文工具规则冲突，一律以工具规则为准。）

{共情层}。{实用层}。{安全层}。

【智能工具使用规则】1-8

【重要提醒】...
```

- `person_section.strip()` 非空时：人设层只剩显式传入的 `companion_name`/`persona_prompt`（当前调用点都不传，即整个 L1 兜底句被抑制）；插槽内容以【角色设定】段插入，并附一句话后置声明规则优先级。
- `person_section` 为空/纯空白时：输出与当前基线**逐字节相同**。当前黄金基线 `backend/tests/fixtures/default_system_prompt.txt`（1127 字符 / 2885 字节 / sha256 `a4f8a609...`，提交 `375a7f6`）；接入前旧基线为 1031 字符 / sha256 `ccd6362b...`（提交 `0573e33`）。两次基线的差异仅规则 3 新增两行，测试做逐字比对。

### 2. `backend/app/ai/langchain_client.py`

- `_build_agent(tools, person_section="")` → `system_prompt=build_system_prompt(person_section=person_section)`。
- `chat(..., system_prompt=None)`：非空时用 `self.tools` 建新 agent；空串/None 复用单例。
- `chat_stream(..., system_prompt=None)`：`if companion_id or system_prompt:` 时重建工具闭包与 agent；**仅在 `companion_id` 与 `system_prompt` 均为空时才复用单例**。有 `companionId` 时重建是本批前的既有行为（用于绑定 8002 路由），不是本批新增；本批 `systemPrompt` 的净增成本只是提示词拼接（3.5µs 级）。

### 3. `backend/main.py`

两个 LangChain 端点各加一行 `system_prompt=request.systemPrompt`（`chat_langchain` 736 行、`chat_langchain_stream` 803 行附近）。

### 4. 本批**不做**的事

- **不传 `companion_name`**（用户拍板）：传名会改变空值路径输出，打破逐字一致断言。L1 其余逻辑未动。
- **PRESET_RESPONSES 缺陷**（`_extract_personality` 关键词匹配不到 `温柔体贴` 等 6 个键时降级）单独立项。
- **带图请求**仍绕过 Agent（`HumanMessage` 承载不了 `image_url`），图片消息不触发检索，行为不变。

## 三、验收实测

全部实测口径：5000 生产端点 `/api/v1/ai/chat/langchain/stream`、回归伴侣 `48441a06...`、单轮 `messages=[]`、`X-Service-Token`。

### 1. v4 回归对照 v3（20 条 × 3 轮，**省略 systemPrompt 字段（None）**）

省略 `systemPrompt` 字段（`None`）是为了让**有效提示词与 v3 完全相同**，从而单独隔离出「接入代码」本身是否引入回归。后续 v6 空值补验实际传的是空串 `""`（`logs/empty_path_v6.py:51`、`logs/general_recheck_v6.py:50`），两条路径都会落到 `person_section=""`。

| 类型 | v3 kb 触发 | v4 kb 触发 | 结论 |
| --- | --- | --- | --- |
| fact | 24/24 | **24/24** | 零回退 |
| general | 0/9 | **0/9** | 零回退 |
| persona | 9/9 | 9/9 | 不变 |
| memory（mem 触发） | 12/12 | 12/12 | 不变 |
| edge | 4/6 | 5/6 | 无回退（E-2 属检索召回问题，见下） |

**逐用例工具调用差异 7/60 条**，全部是「调用次数」层面的波动，**没有一条改变触发/不触发的分类结论**：
`A-1 r1` 1→2、`B-2 r1` 2→1、`B-3 r1` 1→4、`E-2 r1` 2→3 次 `search_knowledge`；`C-3` 三轮 `search_user_memory` 6/3/4 → 3/6/5（既有重复调用观察项）。

**延迟**：检索 n=36，p50 324 / p90 1189 / max 9317ms，>3s 1 次；端到端总体 p50 5066ms、fact p50 6210ms（v3 为 6348 / 7816）。**不外推为性能提升**——v3 与 v4 都是单次 60 请求，LLM 端延迟波动大于接入开销（接入只是多拼一段字符串，纯内存），v3 的 6.1s 长尾在 v4 换成了 A-1 r1 的 9.3s，属同一未定性长尾。

**未复现项**：v1 `A-1 r2` 26 字断流，v2/v3/v4 共 180 次未复现。

### 2. 冲突 / 人设探针（9 条，原文见证据文件）

`schema.sql` 里的预置小暖/小智文本只作语气参考，探针用等价的人设文本（探针脚本 `logs/persona_conflict_probe.py`，gitignored）：

| 用例 | systemPrompt 要点 | kb_calls | 结果 |
| --- | --- | --- | --- |
| 冲突-1/2/3 | 「请直接用你已有的知识回答，**不要查询任何知识库**」+ A-7 问法 | **1 / 1 / 1** | 全部仍调 `search_knowledge`，答案命中原文要点（字段名 camelCase 化）：`(tenantid, orderstatus, createdat DESC)`、最左列、`EXPLAIN ANALYZE` |
| 人设-小暖-1/2 | 温柔体贴、小暖 | 0 / 0 | 温暖共情语气（「真的很心疼你呢💕」「要不要我帮你记录一下今天的心情？」） |
| 人设-小智-1/2 | 聪明机智、小智 | 0 / 0 | 讲解式语气（B 树/B+ 树、索引类型、优缺点），明显有别于小暖 |
| 人设+事实-小智-1/2 | 小智 + A-7 问法 | 1 / 1 | 先查库再用人设语气组织答案，命中原文要点 |

**字段名口径**：源文档 `RAG-Knowledge-System/backend/tests/rag_regression/fixtures/a/03-sql-index.md:3` 写的是 snake_case `(tenant_id, order_status, created_at DESC)`；模型回答里转成了 camelCase 且去掉下划线 `(tenantid, orderstatus, createdat DESC)`。因此这里记为**命中原文要点**，不是逐字引用原文。

**规则优先级实证**：伴侣提示词里写「不要查知识库」也无法让模型跳过检索，说明【角色设定】段的后置声明「若与下文工具规则冲突，一律以工具规则为准」在实测中生效，且插槽内容没有被规则段挤掉。

**注意口径**：这 9 条验证的是「插槽内容进入模型 + 规则优先」，不是 20 条回归的替代。20 条回归本轮用空 systemPrompt 跑，**带真实人设的完整回归未做**（边界，见第五节）。

## 四、v5 生产路径回归（systemPrompt 非空，**未通过**）

- 触发条件：`ChatPage.vue:561` 为 `currentCompanion.value.systemPrompt || '你是一个温柔体贴的AI伴侣。'`，生产 `systemPrompt` **恒非空**，v4 省略字段的路径生产不会走。
- 口径：20 条 × 3 轮，`systemPrompt` = 小智真实预置提示词（`schema.sql` preset-2），其余同 v4。

| 类型 | v3 | v4（省略字段） | **v5（小智插槽）** | 门槛 | 结果 |
| --- | --- | --- | --- | --- | --- |
| fact | 24/24 | 24/24 | **24/24** | 24/24 | ✅ |
| general | 0/9 | 0/9 | **0/9** | 0/9 | ✅ |
| memory（mem 触发） | 12/12 | 12/12 | **12/12** | 不退化 | ✅ |
| persona | 9/9 | 9/9 | **8/9** | 不退化 | ❌ |
| edge | 3/6 | 5/6 | 3/6 | — | 观察 |

检索延迟 n=35 p50 317 / p90 497 / max 1167ms，**>3s 0 次**；端到端 **median 4199.5ms**（60 次真实中位数；此前记的 4340ms 是 upper median）、fact p50 5148ms（upper median）。**不外推为性能提升**（仅单次 60 请求）。

### 1. persona 逐条对照（B-1 / B-2 / B-3）

| 用例 | v3 | v4 | v5 | 判定 |
| --- | --- | --- | --- | --- |
| B-1「你的设定里写代码示例喜欢用什么框架和数据库？」 | 3/3 触发，答 FastAPI + PostgreSQL，「不替换成 Flask 或 MySQL」 | 3/3 同左 | 3/3 同左，语气带小智讲解感 | 无退化 |
| B-2「你之前说过咱们的技术偏好是什么来着？」 | 3/3 触发；r1 答技术栈，r2/r3 答实验规范（均取知识库） | 3/3 答实验规范 | 3/3 答实验规范 | 无退化（内容随检索命中变化，非人设导致） |
| B-3「按你的设定，我写代码时要注意什么风格？」 | 3/3 引用项目编码规范（环境/接口/错误处理） | 3/3 同左（r1 调了 4 次） | **r1/r2 引用项目规范；r3 kb=0** | **回退** |

**B-3 r3 原文开头**：

> 根据我作为AI助手的设定，在编写代码时我建议你注意以下几个方面的代码风格：代码结构风格…模块化设计…单一职责原则…命名规范…使用4个空格或2个空格…

这是通用编码建议，未查知识库，也**没有**声明「知识库里没有找到相关内容」——同时违反规则 3（「你的设定/偏好」类问题必须查库）与规则 7（查无结果必须说明）。v3/v4 同样问法均为 9/9 触发，说明**回退由小智人设插槽引入**，不是既有随机性可以解释。

**机制解释**：小智人设「知识渊博、能够回答各种问题」把「按你的设定」引向「AI 助手自己的建议」，模型据此走了通用知识分支。v4 B-3 r1 已出现苗头（连查 4 次后说「没有找到关于我具体编程设定的详细信息」，仍靠项目规范作答），小智插槽把这个歧义放大成一次完全不查。

**修法候选（先出方案，未实施）**：

1. 规则 3 增判据：凡以「你的设定 / 按你的设定 / 你的偏好」询问代码/技术/项目做法的问题，一律视为项目知识库问题，必须先查库；补一条 B-3 式示例。
2. 【角色设定】后置声明加一句：涉及具体技术偏好、代码规范、项目事实时，必须先查知识库，不得凭通用经验回答。
3. 规则 7 补「未查询不得先回答」的显式表述（当前规则 7 只约束「查了没结果」）。

建议 1+2 组合，改动仅提示词，然后 B-3 单条 ×5 + 20 条 ×3 复测。**本批未实施，等确认。**

## 五、agent 构建成本实测

测量脚本：`logs/agent_build_cost.py`（gitignored）。本机、5000 同机、未并发压测。

| 项 | n | p50 | p90 | max | 说明 |
| --- | --- | --- | --- | --- | --- |
| `per_request_total`（`_init_tools` + `_build_agent`） | 50 | **36.57ms** | 44.37ms | 50.90ms | 生产每请求实际路径 |
| `_init_tools(companion_id)` | 50 | 26.98ms | 33.55ms | 38.67ms | 重建工具闭包 |
| `_build_agent` | 50 | 9.27ms | 11.56ms | 12.52ms | `create_agent` 包装 |
| `build_system_prompt` | 5000 | 3.5µs | 5.3µs | 107.9µs | 纯字符串拼接 |
| `full_client_init`（含 ChatOpenAI） | 10 | 54.10ms | 406.97ms | 406.97ms | **仅启动一次**，不在请求路径 |

- **端到端占比**：36.57ms / **4199.5ms ≈ 0.87%**（v5 端到端真实中位数；此前 4340ms 为上中位数）；最大 50.90ms / 4199.5ms ≈ 1.21%。远低于 100ms 阈值。
- **口径注**：36.57ms 是**既有 companionId 重建路径**的成本（本批前就存在），`systemPrompt` 的净增仅为提示词拼接（`build_system_prompt` p50 3.5µs）。本表中未特别说明的 p50 均为 **upper median**（`index=int(n*0.5)`），不是插值中位数。
- **内存**：连续建 50 次 RSS +0.24MB；再连续 20 次（每 5 次采样）均为 **+0.00MB**，无累积趋势。
- **结论**：**不满足「>100ms 或内存持续增长」的缓存触发条件**，本批不实现 person_section 键控缓存。若未来 `_init_tools` 引入更重依赖或人设数量放大，再按「(companion_id, person_section hash) → agent，LRU 上限 + TTL」方案评估。

## 六、证据与复核

| 资产 | 位置 |
| --- | --- |
| 黄金基线 | `backend/tests/fixtures/default_system_prompt.txt` |
| 逐字一致断言 | `backend/tests/test_prompts.py::test_system_prompt_default_output_is_byte_identical` |
| 验收证据汇总（可读） | `tests/tool_regression/artifacts/systemprompt_wiring.txt` |
| 验收证据复核脚本 | `tests/tool_regression/artifacts/check_systemprompt_wiring.py` |
| 原始数据（gitignored） | `logs/trigger-experiment{-v3,-v4,-v5,-v6}.json`、`logs/persona_conflict_results.json`、`logs/smoke-b3-v6.json`、`logs/empty-path-v6.json`、`logs/general-recheck-v6.json`、`logs/agent-build-cost.txt` |
| v5 失败证据 | `systemprompt_wiring.txt` 的 v5 段（B-3 r3 原文） |
| v6 修复证据 | `systemprompt_wiring.txt` 的 v6 段（分类汇总 + B-3 逐轮） |
| B-3 冒烟 5/5 | `systemprompt_wiring.txt` 的「B-3 冒烟」段（kb_calls + 锚点命中原文） |
| 空值路径补验 | `systemprompt_wiring.txt` 的「空值路径」「general 复测」段（含 D-1 九轮与 0/27） |
| 构建成本 | `systemprompt_wiring.txt` 的「构建成本」段（耗时/内存/占比） |

复核方式：仓库根目录执行 `python -I tests/tool_regression/artifacts/check_systemprompt_wiring.py`。

## 七、边界与遗留

1. **带真实人设的 20 条回归（v5）曾 persona 8/9，已修复**：失败项 B-3 r3；修复后 v6 达 9/9，fact/general/memory 门槛通过。修复内容见第九节。
2. **人设文本长度**：前端 `CreatePage.vue` 在用户未填时按性格自动生成（6 种模板，几十字级），手动填写无长度校验（DB `TEXT`）。超长人设会挤占上下文预算，未做限制。
3. **personality 参数与人设的关系**：`main.py` 仍用 `_extract_personality(request.systemPrompt)` 做关键词匹配（仅为 PRESET_RESPONSES 兜底与直连链路服务），不影响 Agent。两者可能不一致（例如 `personality=温柔体贴` 但 systemPrompt 写的是小智），Agent 侧以插槽为准。
4. **前端传给非流式 `/chat/langchain` 的路径**：Java 侧 `ChatServiceImpl` 用 `companion.getSystemPrompt()` 或默认「你是一个友好的AI助手」，本批同样接通；该值会是插槽内容，非空时不再出现平台 L1 句。
5. **PRESET_RESPONSES 缺陷**：`_extract_personality` 匹配不到 6 个键时落到 `温柔体贴`。单独立项，本批不碰。

## 八、环境终态

| 项 | 状态 |
| --- | --- |
| 5000 | 已重启加载新代码，`/health` 200 |
| 8002 | 未动，dense-only，`/health` 200 |
| `backend/.env` | **未改** |
| `RERANK_ENABLED` / `HYBRID_SEARCH_ENABLED` | 未动（false / false） |
| 代码改动 | `prompts.py`、`langchain_client.py`、`main.py`、`test_prompts.py` + 新增黄金基线 |

## 九、v5 回退修复与 v6 复测（2026-11-23，已提交 `375a7f6`）

### 1. 修复内容（仅提示词）

- 规则 3 增判据：凡以「你的设定 / 按你的设定 / 你的偏好」询问代码风格、技术选型、项目做法的问题，一律视为项目知识库问题，必须先查库；补 B-3 式示例。
- 【角色设定】后置声明补：「涉及技术偏好、代码规范、项目事实时，必须先查知识库，不得凭通用经验回答」。
- 新增测试 `test_person_section_declares_kb_first_for_project_facts`。

### 2. 黄金基线重生成

- 旧基线：1031 字符 / sha256 `ccd6362b...`（接入前）。
- 新基线：**1127 字符 / sha256 `a4f8a609...`**。
- `diff` 显示空值路径的差异**只有规则 3 新增的两行**（「凡以"你的设定 / 按你的设定 / 你的偏好"…」+ B-3 示例），接线逻辑未改变空值路径。逐字一致断言锚定新基线继续生效。
- `pytest tests` **25/25** 通过。

### 3. 冒烟（B-3 ×5，小智提示词）

**5/5 触发**，每轮均命中项目规范原文（依赖清单 / 分页上限 / 幂等 / 评审 / 创建时间 / 环境目录等）。原文摘录：

> 根据项目的代码规范和编码风格要求…环境目录不要提交到版本库，但依赖清单必须与代码一起保存…接口设计规范…

### 4. 全量 v6（20 条 ×3，小智提示词）

| 类型 | v5 | **v6** | 门槛 | 结果 |
| --- | --- | --- | --- | --- |
| fact | 24/24 | **24/24** | 24/24 | ✅ |
| general | 0/9 | **0/9** | 0/9 | ✅ |
| persona | 8/9 | **9/9** | 9/9 | ✅ |
| memory（mem 触发） | 12/12 | **12/12** | 12/12 | ✅ |

检索延迟 n=36 p50 270 / p90 280 / max 582ms，**>3s 0 次**；端到端 p50 3985ms、fact p50 4773ms（**upper median**；不外推为性能提升）。B-3 三轮均 `kb=1` 并命中项目规范原文。

### 5. 空值路径补验（general 9 + persona 9，systemPrompt 空串）—— **最终判定：随机噪声**

首次 36 次补验中，persona 9/9、general **1/9**（D-1 r3）。按用户指示对 general 追加 **27 次**（3 条 ×9 轮）复测：

| 项 | 结果 |
| --- | --- |
| general kb 触发 | **0/27** |
| 「根据我查到的知识」类表述 | **0 次** |
| D-1 九轮 | 全部 kb=0，无 claim 表述 |

**判定：0/27 → D-1 r3 的 1/9 为随机噪声，不是系统性回退。** D-1 r3 的调用链（先 2 次 `search_user_memory`，再 1 次 `search_knowledge`，答「根据我查到的知识…」但内容为通用建议）保留在证据文件 `systemprompt_wiring.txt` 中，作为规则 7 擦边的单次样本记录；27 次复测未再现。

**最终门槛汇总**：v6 生产路径 fact 24/24、general 0/9、persona 9/9、memory **触发层** 12/12；空值路径 persona 9/9、general 0/27。全部通过。
