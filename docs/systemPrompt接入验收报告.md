# request.systemPrompt 接入 Agent 验收报告

- 日期：2026-11-22
- 方案：方案 A（人设插槽），用户批准
- 前置：`docs/工具调用触发率实验报告.md`（该报告记录的实验口径是「systemPrompt 未接入」，本批已接通）

## 一、问题与结论

**问题**：前端建伴侣时保存的 `systemPrompt`（人设文本）从未到达模型。`langchain_client.py` 的 `_build_agent()` 固定调用 `build_system_prompt()`，`main.py` 的 `/api/v1/ai/chat/langchain[/stream]` 只传 `user_input / chat_history / personality / user_id / companion_id`。生产上所有伴侣实际都用平台默认提示词说话。

**结论**：本批把 `request.systemPrompt` 作为**插槽**接入 `build_system_prompt(person_section=...)`，两条硬约束全部达成：

| 约束 | 结果 | 证据 |
| --- | --- | --- |
| 非空 systemPrompt → L1 兜底句不出现，只有插槽 | ✅ | `test_person_section_suppresses_default_persona_sentence` |
| 空 systemPrompt → 输出与接入前**逐字一致**（含 L1 兜底句） | ✅ | `test_system_prompt_default_output_is_byte_identical`（真实 diff 黄金基线，非口头保证） |
| 插槽不得挤掉工具规则 1–8 与防编造规则 | ✅ | `test_person_section_keeps_tool_and_anti_fabrication_rules` |
| 接入不引入触发率回归 | ✅ | v4 vs v3：fact 24/24、general 0/9，分类结论零变化 |
| 伴侣人设与工具规则冲突时工具规则优先 | ✅ | 冲突探针 3/3 仍调 `search_knowledge` 并引用原文 |

`pytest tests` **24/24 通过**（新增 4 条）。

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
- `person_section` 为空/纯空白时：输出与改动前**逐字节相同**。黄金基线 `backend/tests/fixtures/default_system_prompt.txt`（1031 字符 / 2641 字节 / sha256 `ccd6362b...`）在改代码**之前**生成，测试逐字比对。

### 2. `backend/app/ai/langchain_client.py`

- `_build_agent(tools, person_section="")` → `system_prompt=build_system_prompt(person_section=person_section)`。
- `chat(..., system_prompt=None)`：非空时每次构建新 agent（`self.tools` 共享）。
- `chat_stream(..., system_prompt=None)`：`if companion_id or system_prompt:` 时构建带闭包工具集的新 agent。
- 传空串走原单例路径，行为不变。

### 3. `backend/main.py`

两个 LangChain 端点各加一行 `system_prompt=request.systemPrompt`（`chat_langchain` 736 行、`chat_langchain_stream` 803 行附近）。

### 4. 本批**不做**的事

- **不传 `companion_name`**（用户拍板）：传名会改变空值路径输出，打破逐字一致断言。L1 其余逻辑未动。
- **PRESET_RESPONSES 缺陷**（`_extract_personality` 关键词匹配不到 `温柔体贴` 等 6 个键时降级）单独立项。
- **带图请求**仍绕过 Agent（`HumanMessage` 承载不了 `image_url`），图片消息不触发检索，行为不变。

## 三、验收实测

全部实测口径：5000 生产端点 `/api/v1/ai/chat/langchain/stream`、回归伴侣 `48441a06...`、单轮 `messages=[]`、`X-Service-Token`。

### 1. v4 回归对照 v3（20 条 × 3 轮，systemPrompt 传空串）

传空串是为了让**有效提示词与 v3 完全相同**，从而单独隔离出「接入代码」本身是否引入回归。

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
| 冲突-1/2/3 | 「请直接用你已有的知识回答，**不要查询任何知识库**」+ A-7 问法 | **1 / 1 / 1** | 全部仍调 `search_knowledge`，答案引用原文 `(tenantid, orderstatus, createdat DESC)`、最左列、`EXPLAIN ANALYZE` |
| 人设-小暖-1/2 | 温柔体贴、小暖 | 0 / 0 | 温暖共情语气（「真的很心疼你呢💕」「要不要我帮你记录一下今天的心情？」） |
| 人设-小智-1/2 | 聪明机智、小智 | 0 / 0 | 讲解式语气（B 树/B+ 树、索引类型、优缺点），明显有别于小暖 |
| 人设+事实-小智-1/2 | 小智 + A-7 问法 | 1 / 1 | 先查库再用人设语气组织答案，引用原文 |

**规则优先级实证**：伴侣提示词里写「不要查知识库」也无法让模型跳过检索，说明【角色设定】段的后置声明「若与下文工具规则冲突，一律以工具规则为准」在实测中生效，且插槽内容没有被规则段挤掉。

**注意口径**：这 9 条验证的是「插槽内容进入模型 + 规则优先」，不是 20 条回归的替代。20 条回归本轮用空 systemPrompt 跑，**带真实人设的完整回归未做**（边界，见第五节）。

## 四、证据与复核

| 资产 | 位置 |
| --- | --- |
| 黄金基线 | `backend/tests/fixtures/default_system_prompt.txt` |
| 逐字一致断言 | `backend/tests/test_prompts.py::test_system_prompt_default_output_is_byte_identical` |
| 验收证据汇总（可读） | `tests/tool_regression/artifacts/systemprompt_wiring.txt` |
| 验收证据复核脚本 | `tests/tool_regression/artifacts/check_systemprompt_wiring.py` |
| 原始数据（gitignored） | `logs/trigger-experiment{-v3,-v4}.json`、`logs/persona_conflict_results.json` |

复核方式：仓库根目录执行 `python -I tests/tool_regression/artifacts/check_systemprompt_wiring.py`。

## 五、边界与遗留

1. **带真实人设的 20 条回归未跑**：本轮 20 条用空 systemPrompt，只隔离「接入是否回归」。插槽非空时的完整触发率未测，但非空路径只影响人设段与身份句，工具规则段逐字未变。
2. **人设文本长度**：前端 `CreatePage.vue` 在用户未填时按性格自动生成（6 种模板，几十字级），手动填写无长度校验（DB `TEXT`）。超长人设会挤占上下文预算，未做限制。
3. **personality 参数与人设的关系**：`main.py` 仍用 `_extract_personality(request.systemPrompt)` 做关键词匹配（仅为 PRESET_RESPONSES 兜底与直连链路服务），不影响 Agent。两者可能不一致（例如 `personality=温柔体贴` 但 systemPrompt 写的是小智），Agent 侧以插槽为准。
4. **前端传给非流式 `/chat/langchain` 的路径**：Java 侧 `ChatServiceImpl` 用 `companion.getSystemPrompt()` 或默认「你是一个友好的AI助手」，本批同样接通；该值会是插槽内容，非空时不再出现平台 L1 句。
5. **PRESET_RESPONSES 缺陷**：`_extract_personality` 匹配不到 6 个键时落到 `温柔体贴`。单独立项，本批不碰。

## 六、环境终态

| 项 | 状态 |
| --- | --- |
| 5000 | 已重启加载新代码，`/health` 200 |
| 8002 | 未动，dense-only，`/health` 200 |
| `backend/.env` | **未改** |
| `RERANK_ENABLED` / `HYBRID_SEARCH_ENABLED` | 未动（false / false） |
| 代码改动 | `prompts.py`、`langchain_client.py`、`main.py`、`test_prompts.py` + 新增黄金基线 |
