"""systemPrompt 接入验收证据（只读，可复核）。

1. 黄金基线：空 person_section 与接入前逐字一致（由 pytest 断言，本文件只记录指纹）。
2. v4 回归：与 v3 基线逐用例对比工具调用。
3. 冲突 / 人设探针：9 条用例的 kb_calls 与答案原文。

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
