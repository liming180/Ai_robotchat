"""手动测试脚本：朴素问法 + 用户记忆问法，验证工具选择是否正确。

用法：
    cd backend
    python tests/manual_rag_tool_test.py

依赖：5000 / 8002 都已启动。
"""
import json
import urllib.request

URL = "http://localhost:5000/api/v1/ai/chat/langchain/stream"
TOKEN = "dev-token-2026"


def ask(message: str, companion_id: str = "preset-2", user_id: str = "test-user") -> str:
    body = {
        "userMessage": message,
        "systemPrompt": "你是一个温柔体贴的AI伴侣",
        "messages": [],
        "companionId": companion_id,
        "userId": user_id,
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Service-Token": TOKEN,
        },
        method="POST",
    )
    full = ""
    with urllib.request.urlopen(req, timeout=90) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if line.startswith("data: "):
                try:
                    p = json.loads(line[6:])
                    full += p.get("delta", "")
                except Exception:
                    pass
    return full


def run(label: str, message: str, expect_keywords: list, companion_id: str = "preset-2"):
    print(f"\n=== {label} ===")
    print(f"问: {message}")
    try:
        reply = ask(message, companion_id=companion_id)
        print(f"答: {reply[:400]}")
        hits = [k for k in expect_keywords if k in reply]
        print(f"命中关键词: {hits} ({len(hits)}/{len(expect_keywords)})")
        return reply
    except Exception as e:
        print(f"请求失败: {e}")
        return ""


if __name__ == "__main__":
    print("=" * 60)
    print("A. 朴素问法（应走 search_knowledge，命中麻辣烫等要点）")
    print("=" * 60)
    for i in range(1, 4):
        run(f"A{i}", "小智喜欢吃什么", expect_keywords=["麻辣烫", "微辣", "香菜"])

    print("\n" + "=" * 60)
    print("B. 用户记忆问法（应走 search_user_memory）")
    print("=" * 60)
    run("B1", "我平时喜欢干什么", expect_keywords=[])
    run("B2", "上次我们聊了什么", expect_keywords=[])
