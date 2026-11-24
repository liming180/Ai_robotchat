"""RAG 真实 API 数据导入与检索回归。

用法（在 RAG-Knowledge-System/backend 下执行）：
  # 密码只从进程环境读取，禁止作为命令行参数或写入文件
  $env:RAG_TEST_PASSWORD = '<本次测试密码>'
  python -I tests/rag_regression/run_regression.py --setup --mode dense \
      --state-file D:\Ai_robotchat\logs\rag-regression-state.json

后续只跑预期结果表：
  python -I tests/rag_regression/run_regression.py --verify-only --mode dense \
      --state-file <临时状态文件>

BM25 混合检索（2026-11-22，灰度）：8002 以 HYBRID_SEARCH_ENABLED=true 启动后，
用 --mode hybrid 走另一套伴侣/知识库（名称带 -HYBRID），数据导入到 kb_chunks_hybrid：
  python -I tests/rag_regression/run_regression.py --setup --mode hybrid \
      --state-file D:\Ai_robotchat\logs\rag-regression-state-hybrid.json

脚本只操作名称带「RAG回归」的伴侣及对应知识库，不动已有业务数据。
两种模式的判定口径不同，见 README「判定标准」：
- dense ：top1 是预期文档且含事实；禁止项按 TEI/COSINE 分数（0~1）判定
- hybrid：同样 top1 命中，但禁止项按 RRF 名次分判定；分数只展示、不逐条比对
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CASES_FILE = Path(__file__).resolve().parent / "expected_results.json"
RAG_BASE = os.getenv("RAG_BASE_URL", "http://127.0.0.1:8002").rstrip("/")
JAVA_BASE = os.getenv("JAVA_BASE_URL", "http://127.0.0.1:8081").rstrip("/")
COMPANIONS = {
    "a": {"name": "RAG回归-学习助手", "domain": "编程、学习方法与工程实践"},
    "b": {"name": "RAG回归-生活管家", "domain": "饮食、居家日程与健康生活"},
}
HYBRID_SUFFIX = "-HYBRID"

# 禁止项判定的分数口径：非 top1 位置需要达到该分数才算「有效命中」。
# dense（COSINE/TEI，0~1）：实测正例 0.94~0.999、噪声 ≤0.03；生产 retrieve_score_threshold
# 默认 0.0（更宽松）。
FORBIDDEN_HIT_SCORE = 0.5
# hybrid（RRF 名次分，0.01~0.04 量级）：**阈值随尺度重定**，不能沿用 0.5。
# 2026-11-22 实测（28 条用例、112 条返回）呈两档分布、中间无过渡值：
#   单路命中档 0.0156~0.0164；双路同时命中档 0.0288~0.0328。
# 取 0.0195 落在两档之间，语义是「两路都召回才算有效命中」，
# **不是**「相关/不相关」的语义分界（RRF 尺度给不出后者，详见验收报告）。
# 实测依据：禁止项 NEGATIVE-B-01 实测最高 0.0164（仅 dense 单路弱命中），判通过。
FORBIDDEN_HIT_SCORE_RRF = 0.0195

# 各模式下服务端应返回的分数尺度标签，用来证明 8002 确实跑在预期模式上
# （dense 允许 cosine 或 tei：取决于 RERANK_ENABLED）。
ALLOWED_SCORE_SCALES = {"dense": {"cosine", "tei"}, "hybrid": {"rrf"}}


def companion_names(mode: str) -> dict[str, dict[str, str]]:
    """按模式给伴侣/知识库名加后缀，两套资产互不覆盖。"""
    suffix = HYBRID_SUFFIX if mode == "hybrid" else ""
    return {
        key: {**info, "name": info["name"] + suffix}
        for key, info in COMPANIONS.items()
    }


def _read_service_token() -> str:
    """读取 8002 的 X-Service-Token：环境变量 → 本地文件 → 空（不改动调用）。

    沿用密码通道规矩：不硬编码、不打印内容。
    """
    token = os.environ.get("SERVICE_TOKEN", "").strip()
    if token:
        return token
    path = Path(os.environ.get("SERVICE_TOKEN_FILE", r"D:\Ai_robotchat\logs\.rag_service_token"))
    if path.is_file():
        return path.read_text(encoding="utf-8-sig").strip()
    # 兜底：直接从 8002 自己的 .env 读取（同机测试场景，值不出现在输出中）
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if line.startswith("SERVICE_TOKEN="):
                return line.split("=", 1)[1].strip()
    return ""


class Api:
    def __init__(self, token: str, service_token: str = ""):
        self.token = token
        self.service_token = service_token

    def _headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        if self.service_token:
            headers["X-Service-Token"] = self.service_token
        return headers

    def request(self, method: str, base: str, path: str, **kwargs) -> Any:
        headers = dict(kwargs.pop("headers", {}))
        headers.update(self._headers())
        with httpx.Client(timeout=300, trust_env=False) as client:
            response = client.request(method, base + path, headers=headers, **kwargs)
        try:
            body = response.json()
        except ValueError as exc:
            raise AssertionError(f"{method} {path} 非 JSON：HTTP {response.status_code}") from exc
        if response.status_code >= 400 or not body.get("success", body.get("code") == 200):
            raise AssertionError(f"{method} {path} 失败：HTTP {response.status_code} {body.get('message')}")
        return body.get("data")

    def rag(self, method: str, path: str, **kwargs) -> Any:
        return self.request(method, RAG_BASE, "/api/v1/kb" + path, **kwargs)

    def rag_raw(self, method: str, path: str, **kwargs) -> tuple[int, dict]:
        """返回 (HTTP 状态码, 响应体)；读取超时返回 (0, {message: "client timeout"})。"""
        headers = dict(kwargs.pop("headers", {}))
        headers.update(self._headers())
        try:
            # Milvus rerank deadline 源码硬编码 30s；给 90s 余量，避免 HTTP 客户端
            # 比服务端更早放弃而把「服务端已超时」误报成客户端超时。
            with httpx.Client(timeout=httpx.Timeout(90.0, connect=10.0), trust_env=False) as client:
                response = client.request(method, RAG_BASE + "/api/v1/kb" + path, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            return 0, {"message": f"client timeout: {type(exc).__name__}"}
        try:
            body = response.json()
        except ValueError:
            body = {}
        return response.status_code, body

    def java(self, method: str, path: str, **kwargs) -> Any:
        return self.request(method, JAVA_BASE, "/api/v1" + path, **kwargs)


def _read_password() -> str:
    """密码获取顺序：环境变量 → 本地文件 → getpass 盲打；全程不打印内容。

    本地文件路径默认 D:\\Ai_robotchat\\logs\\.rag_test_pw，可用 RAG_TEST_PW_FILE 覆盖。
    文件由用户本地一次性创建，本脚本只读取、不输出、不写回。
    """
    password = os.environ.get("RAG_TEST_PASSWORD")
    if password:
        return password

    pw_file = Path(os.environ.get("RAG_TEST_PW_FILE", r"D:\Ai_robotchat\logs\.rag_test_pw"))
    if pw_file.is_file():
        # utf-8-sig 兼容 PowerShell Set-Content 写入的 BOM
        password = pw_file.read_text(encoding="utf-8-sig").strip()
        if password:
            return password

    if not sys.stdin.isatty():
        raise SystemExit("密码未配置：请设置 RAG_TEST_PASSWORD 或创建本地密码文件；当前 stdin 非交互终端")
    from getpass import getpass
    return getpass("请输入本次 RAG 测试账号密码（输入不回显）：")


def login() -> tuple[str, str]:
    email = os.environ.get("RAG_TEST_EMAIL")
    if not email:
        raise SystemExit("请从进程环境设置 RAG_TEST_EMAIL；密码不落盘")
    password = _read_password()
    if not password:
        raise SystemExit("密码为空，停止回归")
    with httpx.Client(timeout=30, trust_env=False) as client:
        response = client.post(RAG_BASE + "/api/v1/auth/login", json={"email": email, "password": password})
    body = response.json()
    if response.status_code != 200 or not body.get("success"):
        raise SystemExit(f"测试账号登录失败：HTTP {response.status_code} {body.get('message')}")
    data = body["data"]
    return data["accessToken"], data["user"]["id"]


def upload_collection(api: Api, companion_key: str, collection_id: str) -> list[dict[str, Any]]:
    files = []
    paths = sorted((FIXTURES / companion_key).glob("*.md"))
    if len(paths) != 9:
        raise AssertionError(f"{companion_key} 应有 9 篇文档，实际 {len(paths)}")
    for path in paths:
        files.append(("files", (path.name, path.read_bytes(), "text/markdown; charset=utf-8")))
    uploaded = api.rag("POST", f"/collections/{collection_id}/documents/upload", files=files)
    if len(uploaded) != len(paths):
        raise AssertionError(f"上传数量不一致：{len(uploaded)} / {len(paths)}")
    for item, path in zip(uploaded, paths):
        item["fileNameExpected"] = path.name
    return uploaded


def wait_tasks(api: Api, uploads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending = {item["taskId"]: item for item in uploads}
    finished = []
    deadline = time.monotonic() + 600
    while pending and time.monotonic() < deadline:
        for task_id, item in list(pending.items()):
            task = api.rag("GET", f"/tasks/{task_id}")
            if task["status"] in ("completed", "failed"):
                task["expectedFileName"] = item["fileNameExpected"]
                finished.append(task)
                del pending[task_id]
        if pending:
            time.sleep(2)
    if pending:
        raise AssertionError(f"入库任务超时：{len(pending)} 个")
    return finished


def _retrieve_with_retry(api: Api, payload: dict) -> tuple[dict | None, dict]:
    """单条 rerank 超时重试一次（间隔 2s），原始失败与重试结果都记录。

    只对「HTTP 500 且信息含 rerank / deadline」或客户端超时重试；
    重试后仍失败则返回 (None, record)，由调用方记为失败并继续跑后续用例，
    不中断整轮回归。其他错误立即抛出，不掩盖。
    """
    record = {"firstAttempt": None, "retried": False, "retryResult": None}

    def _is_timeout(status: int, body: dict) -> bool:
        message = (body.get("message") or "").lower()
        return (status == 500 and ("rerank" in message or "deadline" in message)) or (
            status == 0 and "timeout" in message
        )

    status, body = api.rag_raw("POST", "/retrieve", json=payload)
    record["firstAttempt"] = {"status": status, "message": (body.get("message") or "")[:200]}
    if status < 400 and body.get("success"):
        return body["data"], record
    if not _is_timeout(status, body):
        raise AssertionError(f"retrieve 失败(不重试)：HTTP {status} {(body.get('message') or '')[:160]}")

    time.sleep(2)
    record["retried"] = True
    status2, body2 = api.rag_raw("POST", "/retrieve", json=payload)
    record["retryResult"] = {"status": status2, "message": (body2.get("message") or "")[:200]}
    if status2 < 400 and body2.get("success"):
        return body2["data"], record
    return None, record


def verify_retrieve(
    api: Api,
    cases: list[dict[str, Any]],
    state: dict[str, Any],
    mode: str = "dense",
    on_result=None,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    forbidden_threshold = (
        FORBIDDEN_HIT_SCORE_RRF if mode == "hybrid" else FORBIDDEN_HIT_SCORE
    )
    results = []
    expected_scales = ALLOWED_SCORE_SCALES[mode]
    for case in cases:
        data, retry_record = _retrieve_with_retry(api, {
            # topK 默认 8，与生产 5000 链路（LLMConfig.RAG_TOP_K 默认 8）对齐；
            # 可用 --top-k 覆盖。dense-only 下无 rerank 调用，8 块不存在 30s deadline 风险
            # （该限制仅 RERANK_ENABLED=true 时生效）。
            "companionId": state["companions"][case["companion"]]["companionId"],
            "query": case["query"], "topK": top_k, "scoreThreshold": 0,
        })
        if data is None:
            results.append({
                "id": case["id"], "type": case["type"], "query": case["query"],
                "expectedDocument": case.get("expectedDocument"),
                "top1": None, "allHits": [], "elapsedMs": None,
                "passed": False, "failures": ["retrieve 两次均超时（含重试 1 次）"],
                "retry": retry_record,
                "note": "超时判失败，不视为命中",
            })
            print(f"{case['id']}: FAIL 两次均超时（含重试1次）", flush=True)
            if on_result:
                on_result(results[-1])
            continue
        chunks = data["chunks"]
        top = chunks[0] if chunks else None
        # 短文档文档名来自原始文件标题，长文档标题来自 Markdown 一级标题。
        expected_name = Path(case.get("expectedDocument", "")).stem
        matched = [c for c in chunks if expected_name and (
            expected_name in (c.get("documentTitle") or "") or
            (expected_name.startswith("09-") and "手册" in (c.get("documentTitle") or ""))
        )]
        failures = []
        # 模式自证：8002 返回的 scoreScale 必须在预期集合内，否则说明服务端跑的是另一条路径
        # （比如开了 hybrid 却仍在 dense 判定，或 RERANK_ENABLED 状态与预期不符），
        # 此时所有分数结论都不可信，直接判该条失败而不是静默按错的尺度比较。
        score_scale = data.get("scoreScale")
        if score_scale not in expected_scales:
            failures.append(
                f"分数尺度不符：期望 {sorted(expected_scales)}，实际 {score_scale}"
            )
        if case["type"] in ("fact", "semantic", "interference", "long", "contrast"):
            if not top:
                failures.append("零命中")
            elif not matched or top.get("documentId") != matched[0].get("documentId"):
                failures.append(f"top1 不是预期文档：{case['expectedDocument']}")
            elif case["expectedText"] not in top.get("content", ""):
                failures.append(f"top1 不含预期事实：{case['expectedText']}")
        # 禁止项口径：禁止文档分数 ≥ 模式阈值才算有效命中。不按位置判定：否定/隔离
        # 用例常出现全部命中同分的并列情形，此时排名只是噪声，位置不携带置信信息。
        # dense 阈值 0.5 依据正例 0.94~0.999 / 噪声 ≤0.03；
        # hybrid 阈值随 RRF 尺度重定（见 FORBIDDEN_HIT_SCORE_RRF 与验收报告实测数据）。
        for chunk in chunks:
            for forbidden in case.get("forbiddenDocuments", []):
                if Path(forbidden).stem not in (chunk.get("documentTitle") or ""):
                    continue
                score = float(chunk.get("score") or 0.0)
                if score >= forbidden_threshold:
                    failures.append(f"命中禁止文档：{forbidden}（分数 {score}）")
            if case.get("expectNoDocument") and case["companion"] == "a":
                if any(word in chunk.get("content", "") for word in ("南瓜小米粥", "北豆腐", "家庭预约")):
                    failures.append("跨伴侣命中生活知识")
            if case.get("expectNoDocument") and case["companion"] == "b":
                if any(word in chunk.get("content", "") for word in ("FastAPI", "PostgreSQL", "tenant_id")):
                    failures.append("跨伴侣命中编程知识")
        results.append({
            "id": case["id"], "type": case["type"], "query": case["query"],
            "expectedDocument": case.get("expectedDocument"),
            "top1": top, "allHits": [{"documentTitle": c.get("documentTitle"), "chunkIndex": c.get("chunkIndex"), "score": c.get("score"), "content": c.get("content")} for c in chunks],
            "elapsedMs": data["elapsedMs"], "scoreScale": score_scale,
            "passed": not failures, "failures": failures,
            "retry": retry_record,
            "note": f"{mode} 模式：禁止项阈值 {forbidden_threshold}；分数只展示不参与逐条比对",
        })
        retry_tag = " [重试1次]" if retry_record["retried"] else ""
        print(
            f"{case['id']}: {'PASS' if not failures else 'FAIL'} "
            f"top1={top.get('score') if top else '-'} {top.get('documentTitle') if top else '-'} "
            f"{failures}{retry_tag}"
        )
        if on_result:
            on_result(results[-1])
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true", help="登录、建两个伴侣和知识库并导入 18 篇文档")
    parser.add_argument("--verify-only", action="store_true", help="只执行预期结果表")
    parser.add_argument(
        "--mode", choices=["dense", "hybrid"], default="dense",
        help="dense=kb_chunks 单路（默认）；hybrid=kb_chunks_hybrid + BM25（需 8002 开 HYBRID_SEARCH_ENABLED）",
    )
    parser.add_argument("--state-file", type=Path, required=True, help="临时运行 ID 与结果；不含凭据")
    parser.add_argument(
        "--top-k", type=int, default=8,
        help="单次检索召回块数（默认 8，与生产 5000 链路一致；对照旧口径可传 4）",
    )
    args = parser.parse_args()
    if not args.setup and not args.verify_only:
        parser.error("请选择 --setup 或 --verify-only")
    if args.state_file.exists() and not args.verify_only:
        raise SystemExit("状态文件已存在，为避免重复建库已停止；请换一个新路径")

    token, user_id = login()
    api = Api(token, _read_service_token())
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]
    state = {"runId": uuid.uuid4().hex, "userId": user_id, "companions": {}}
    if args.verify_only:
        state = json.loads(args.state_file.read_text(encoding="utf-8"))
        if state.get("mode", "dense") != args.mode:
            raise SystemExit(
                f"状态文件是 {state.get('mode', 'dense')} 模式建的，与 --mode {args.mode} 不符；"
                "换用对应模式的状态文件，或用新路径重跑 --setup"
            )
    else:
        state["mode"] = args.mode
        for key, info in companion_names(args.mode).items():
            existing = [c for c in api.java("GET", "/companions") if c["name"] == info["name"]]
            if existing:
                raise AssertionError(f"已有同名回归伴侣，为避免误删停止：{info['name']}")
            companion = api.java("POST", "/companions", json={
                "name": info["name"], "avatar": "", "description": info["domain"],
                "category": "RAG回归", "personality": info["domain"],
                "systemPrompt": "只用于 RAG 知识库回归；回答未知内容时明确说明不知道。", "tags": "RAG回归,自动化验收",
            })
            collection = api.rag("POST", "/collections", json={
                "name": info["name"] + "-知识库", "description": "可复用真实 API 回归资产",
                "companionId": companion["id"], "chunkSize": 500, "chunkOverlap": 50,
            })
            state["companions"][key] = {"companionId": companion["id"], "collectionId": collection["id"]}
            args.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            uploads = upload_collection(api, key, collection["id"])
            tasks = wait_tasks(api, uploads)
            state["companions"][key]["tasks"] = tasks
            args.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{key}: 导入完成 {len(tasks)} 篇，切片 {sum(t['chunkCount'] for t in tasks)}")

    # 每条完成即落盘：中途崩溃也不丢已得结果，重跑时可直接比对。
    state["results"] = []

    def _save_one(result: dict) -> None:
        state["results"].append(result)
        args.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    # 只跑目标用例，--setup（建库导入）与 --verify-only（27 条检索）互不混合。
    verify_retrieve(api, cases, state, mode=args.mode, on_result=_save_one, top_k=args.top_k)
    args.state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成：{sum(r['passed'] for r in state['results'])}/{len(state['results'])}；结果不含账号密码或 token")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"回归异常：{type(exc).__name__}: {exc}", file=sys.stderr)
        raise
