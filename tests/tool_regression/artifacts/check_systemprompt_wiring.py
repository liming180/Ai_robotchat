"""systemPrompt 接入验收证据（只读，可复核）。

1. 黄金基线：空 person_section 与接入前逐字一致（由 pytest 断言，本文件只记录指纹）。
2. v4 回归：与 v3 基线逐用例对比工具调用（空 systemPrompt）。
3. v5 生产路径：小智真实提示词（非空），重点看 persona B-3。
4. 冲突 / 人设探针：9 条用例的 kb_calls 与答案原文。

用法：仓库根目录 `python -I tests/tool_regression/artifacts/check_systemprompt_wiring.py`
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LOGS = ROOT / "logs"


def load(name):
    return json.loads((LOGS / name).read_text(encoding="utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    golden = ROOT / "backend/tests/fixtures/default_system_prompt.txt"
    raw = golden.read_bytes()
    print("[golden] len=%d sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))

    v3 = {(x["id"], x["round"]): x for x in load("trigger-experiment-v3.json")}
    v4 = {(x["id"], x["round"]): x for x in load("trigger-experiment-v4.json")}
    v5 = {(x["id"], x["round"]): x for x in load("trigger-experiment-v5.json")}
    diff = [(k, v3[k]["kb_calls"], v3[k]["mem_calls"], v4[k]["kb_calls"], v4[k]["mem_calls"])
            for k in sorted(v3)
            if (v3[k]["kb_calls"], v3[k]["mem_calls"]) != (v4[k]["kb_calls"], v4[k]["mem_calls"])]
    print("[v4-vs-v3] 工具调用不一致 %d/%d 条：" % (len(diff), len(v3)))
    for k, k3, m3, k4, m4 in diff:
        print("  %s r%d  v3 kb=%d mem=%d  ->  v4 kb=%d mem=%d" % (k[0], k[1], k3, m3, k4, m4))
    for kind in ("fact", "general"):
        line = []
        for n, rows in (("v3", v3), ("v4", v4)):
            hit = sum(1 for x in rows.values() if x["kind"] == kind and x["kb_calls"] > 0)
            tot = sum(1 for x in rows.values() if x["kind"] == kind)
            line.append("%s %d/%d" % (n, hit, tot))
        print("[%s] kb 触发 %s" % (kind, " -> ".join(line)))

    print("\n[v5] 生产路径 systemPrompt=小智真实提示词（非空）")
    for kind in ("fact", "persona", "memory", "general", "edge"):
        rows = [x for x in v5.values() if x["kind"] == kind]
        kb = sum(1 for x in rows if x["kb_calls"] > 0)
        mm = sum(1 for x in rows if x["mem_calls"] > 0)
        print("  %-7s n=%d kb=%d/%d mem=%d/%d" % (kind, len(rows), kb, len(rows), mm, len(rows)))
    print("[v5] persona 逐轮：")
    for k in sorted(v5):
        if v5[k]["kind"] == "persona":
            print("  %s r%d kb=%d" % (k[0], k[1], v5[k]["kb_calls"]))
    print("[v5] B-3 r3 原文（失败项）：")
    bad = v5.get(("B-3", 3))
    if bad:
        print(bad["answer"].strip())

    v6 = {(x["id"], x["round"]): x for x in load("trigger-experiment-v6.json")}
    print("\n[v6] 修复后生产路径（小智提示词）")
    for kind in ("fact", "persona", "memory", "general", "edge"):
        rows = [x for x in v6.values() if x["kind"] == kind]
        kb = sum(1 for x in rows if x["kb_calls"] > 0)
        mm = sum(1 for x in rows if x["mem_calls"] > 0)
        print("  %-7s n=%d kb=%d/%d mem=%d/%d" % (kind, len(rows), kb, len(rows), mm, len(rows)))
    print("[v6] B-3 逐轮：")
    for k in sorted(v6):
        if k[0] == "B-3":
            print("  r%d kb=%d" % (k[1], v6[k]["kb_calls"]))

    empty = load("empty-path-v6.json")
    print("\n[空值路径补验] general 9 + persona 9（systemPrompt 空串）")
    for kind in ("persona", "general"):
        rows = [x for x in empty if x["kind"] == kind]
        print("  %-7s kb=%d/%d" % (kind, sum(1 for x in rows if x["kb_calls"] > 0), len(rows)))
    print("[空值路径] D-1 三轮：")
    for x in empty:
        if x["id"] == "D-1":
            print("  r%d kb=%d mem=%d" % (x["round"], x["kb_calls"], x["mem_calls"]))

    recheck = load("general-recheck-v6.json")
    print("\n[general 复测] 3 条 ×9 轮")
    print("  kb 触发 %d/%d" % (sum(1 for x in recheck if x["kb_calls"] > 0), len(recheck)))
    print("[general 复测]「根据我查到的知识」类表述：")
    hits = [(x["id"], x["round"], x["claim_phrases"]) for x in recheck if x["claim_phrases"]]
    print("  " + (str(hits) if hits else "0 次"))
    print("[general 复测] D-1 九轮：")
    for x in recheck:
        if x["id"] == "D-1":
            print("  r%d kb=%d claim=%s" % (x["round"], x["kb_calls"], x["claim_phrases"]))

    smoke = load("smoke-b3-v6.json")
    print("\n[B-3 冒烟] 5 轮（小智提示词）")
    for x in smoke:
        print("  r%d kb=%d anchors=%s" % (x["run"], x["kb_calls"], x["anchors"]))

    probe = load("persona_conflict_results.json")
    print("[probe] 9 条")
    for x in probe:
        print("  %s kb_calls=%d len=%d" % (x["name"], x["kb_calls"], len(x["answer"])))
    print("\n[probe 原文]")
    for x in probe:
        print("=" * 70)
        print(x["name"], "| kb_calls=%d" % x["kb_calls"])
        print(x["answer"].strip())


if __name__ == "__main__":
    main()
