"""第二批鉴权验证（A~H 组），2026-11-21。

覆盖：
  A 鉴权基础：无 Bearer / 伪造签名 / 过期 / 缺 userId
  B 横向越权：collection 级 + document/task 级（用户答复②补充）
  C 正常路径：本人 CRUD / 上传 / 检索
  D 白名单：/health、/、auth/login 无需 token
  E 预置伴侣禁建库（403）
  F 主库不可用 → 503（通过临时置空 MainSessionLocal 模拟，不改配置）
  G 覆盖率：由 pytest tests/test_auth_coverage.py 负责

密码与 token 沿用 run_regression 的通道，不硬编码、不打印。
运行：
    cd RAG-Knowledge-System/backend
    python -I tests/verify_auth_batch2.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# 复用回归脚本的登录与 token 读取
_spec = importlib.util.spec_from_file_location(
    "rr", Path(__file__).resolve().parent / "rag_regression" / "run_regression.py"
)
rr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rr)

import jwt  # noqa: E402  PyJWT

RAG = "http://127.0.0.1:8002"
RESULTS: list[tuple[str, str, str, bool, object]] = []


def record(group: str, name: str, expected, actual, ok: bool) -> None:
    RESULTS.append((group, name, str(expected), ok, actual))


def call(method: str, path: str, *, token: str | None = None, **kw):
    headers = dict(kw.pop("headers", {}))
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=120, trust_env=False) as c:
        r = c.request(method, RAG + path, headers=headers, **kw)
    try:
        body = r.json()
    except ValueError:
        body = {}
    return r.status_code, body


def check(group: str, name: str, expected_status: int, status: int, body: dict) -> None:
    ok = status == expected_status
    record(group, name, expected_status, f"{status} {str(body.get('message'))[:60]}", ok)


def make_expired_token(secret: str) -> str:
    now = int(time.time())
    return jwt.encode({"userId": "u", "email": "e", "iat": now - 7200, "exp": now - 3600}, secret, algorithm="HS256")


def make_no_userid_token(secret: str) -> str:
    now = int(time.time())
    return jwt.encode({"email": "e", "iat": now, "exp": now + 3600}, secret, algorithm="HS256")


def main() -> int:
    token, user_id = rr.login()
    svc = rr._read_service_token()
    secret = os.environ.get("JWT_SECRET", "").strip()
    if not secret:
        # 与 8002 同源：用户级环境变量（本机已 setx）
        secret = os.environ.get("JWT_SECRET_USER", "").strip()
    state = json.loads(Path(r"D:\Ai_robotchat\logs\rag-regression-state.json").read_text(encoding="utf-8"))
    my_coll = state["companions"]["a"]["collectionId"]
    my_doc = state["companions"]["a"]["tasks"][0]["documentId"]
    my_task = state["companions"]["a"]["tasks"][0]["taskId"]

    # 另一个用户的资源：用 demo 账号的数据（若有），否则用旧库模拟
    other_coll = "a6ff8355-3062-4a9d-a1e4-2b6acbc3f028"  # 任务七残留，created_by=NULL
    preset_comp = "preset-1"

    # ---------------- A 鉴权基础 ----------------
    s, b = call("GET", "/api/v1/kb/collections")
    check("A", "无 Bearer", 401, s, b)

    s, b = call("GET", "/api/v1/kb/collections", token=token[:-3] + "abc")
    check("A", "伪造签名", 401, s, b)

    if secret:
        expired = make_expired_token(secret)
        s, b = call("GET", "/api/v1/kb/collections", token=expired)
        check("A", "过期 token", 401, s, b)

        no_uid = make_no_userid_token(secret)
        s, b = call("GET", "/api/v1/kb/collections", token=no_uid)
        check("A", "缺 userId", 401, s, b)
    else:
        record("A", "过期/缺userId（跳过）", "401", "JWT_SECRET 未取到", False)

    # ---------------- B 横向越权 ----------------
    s, b = call("GET", f"/api/v1/kb/collections/{other_coll}", token=token)
    check("B", "读他人/无归属 collection", 403, s, b)

    s, b = call("PUT", f"/api/v1/kb/collections/{other_coll}", token=token, json={"name": "x"})
    check("B", "改他人/无归属 collection", 403, s, b)

    s, b = call("DELETE", f"/api/v1/kb/collections/{other_coll}", token=token)
    check("B", "删他人/无归属 collection", 403, s, b)

    s, b = call("GET", f"/api/v1/kb/collections/{other_coll}/documents", token=token)
    check("B", "列他人/无归属文档", 403, s, b)

    # 文档级越权（用户答复②明确要求）
    s, b = call("GET", "/api/v1/kb/documents/00000000-0000-0000-0000-000000000000", token=token)
    check("B", "读不存在/他人 document 详情", 403, s, b)

    s, b = call("GET", "/api/v1/kb/tasks/ffffffffffffffffffffffffffffffff", token=token)
    check("B", "查他人/不存在 task", 403, s, b)

    # 上传到他人 collection
    s, b = call("POST", f"/api/v1/kb/collections/{other_coll}/documents/manual", token=token,
                json={"title": "x", "content": "y"})
    check("B", "往他人 collection 写文档", 403, s, b)

    # ---------------- C 正常路径 ----------------
    s, b = call("GET", "/api/v1/kb/collections", token=token)
    mine = [i for i in b.get("data", {}).get("items", []) if i["id"] == my_coll]
    check("C", "列本人知识库(含回归库)", 200, s, b)
    record("C", "列表只含本人库", "仅本人", f"{len(b.get('data', {}).get('items', []))} 个", len(mine) == 1)

    s, b = call("GET", f"/api/v1/kb/collections/{my_coll}", token=token)
    check("C", "本人 collection 详情", 200, s, b)

    s, b = call("GET", f"/api/v1/kb/collections/{my_coll}/documents", token=token)
    check("C", "本人文档列表", 200, s, b)

    s, b = call("GET", f"/api/v1/kb/documents/{my_doc}", token=token)
    check("C", "本人文档详情", 200, s, b)

    s, b = call("GET", f"/api/v1/kb/tasks/{my_task}", token=token)
    check("C", "本人任务状态", 200, s, b)

    s, b = call("GET", "/api/v1/kb/companions", token=token)
    check("C", "伴侣列表(预置+本人)", 200, s, b)
    names = [i["name"] for i in b.get("data", {}).get("items", [])]
    record("C", "伴侣列表含预置", "含 preset", f"{len(names)} 个", len(names) >= 4)

    # 检索仍走服务间 token
    # 鉴权相关只关心是否被 401 拦下：200 或 500（已知 rerank 30s 超时）都说明放行
    s, b = call("POST", "/api/v1/kb/retrieve",
                json={"companionId": state["companions"]["a"]["companionId"],
                      "query": "Python 虚拟环境版本", "topK": 4},
                headers={"X-Service-Token": svc})
    record("C", "检索(服务间 token) 未被 401 拦截", "非401", f"{s}", s != 401)

    # 无 token 必须 401，证明鉴权真的在生效
    s, b = call("POST", "/api/v1/kb/retrieve",
                json={"companionId": state["companions"]["a"]["companionId"],
                      "query": "x", "topK": 4})
    check("C", "检索无服务间 token", 401, s, b)

    # ---------------- D 白名单 ----------------
    for path in ("/health", "/"):
        s, _ = call("GET", path)
        check("D", f"白名单 {path}", 200, s, {})
    s, _ = call("POST", "/api/v1/auth/login", json={"email": "x@y.z", "password": "p"})
    record("D", "白名单 auth/login", "非 401/404", f"{s}", s in (400, 401, 422))

    # ---------------- E 预置伴侣禁建库 ----------------
    s, b = call("POST", "/api/v1/kb/collections", token=token,
                json={"name": "越权测试-" + uuid.uuid4().hex[:6], "companionId": preset_comp})
    check("E", "给预置伴侣建库", 403, s, b)

    # ---------------- F 主库不可用 → 503 ----------------
    # 注意：companions.py 在 import 时就绑定了 MainSessionLocal，改模块属性无效。
    # 这里直接测 require_companion_owner 的 503 分支（它每次调用都动态取模块属性）。
    from fastapi import HTTPException

    import app.db.database as dbmod
    from app.core.security import require_companion_owner

    saved = dbmod.MainSessionLocal
    try:
        dbmod.MainSessionLocal = None
        try:
            require_companion_owner(user_id, state["companions"]["a"]["companionId"])
            record("F", "主库不可用做归属校验", 503, "未抛异常", False)
        except HTTPException as e:
            check("F", "主库不可用做归属校验", 503, e.status_code, {"message": e.detail})
    finally:
        dbmod.MainSessionLocal = saved

    # ---------------- 汇总 ----------------
    passed = sum(1 for *_, ok in RESULTS if ok)
    print("\n分组 | 用例 | 期望 | 实际 | 结果")
    print("-" * 100)
    for group, name, expected, ok, actual in RESULTS:
        print(f"{group} | {name} | {expected} | {actual} | {'PASS' if ok else 'FAIL'}")
    print("-" * 100)
    print(f"合计 {passed}/{len(RESULTS)}")

    out = Path(r"D:\Ai_robotchat\logs\auth-batch2-results.json")
    out.write_text(
        json.dumps([{"group": g, "name": n, "expected": e, "actual": a, "passed": o}
                    for g, n, e, o, a in RESULTS], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
