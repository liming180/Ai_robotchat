"""milvus_rag 权限实测探针（P2-5 动作 3 第 5 步）。

用 milvus_rag 的真实凭据跑一遍 8002 会做的全部操作，并验证高危操作被拒绝。

探针数据用 companion_id=__rbac_probe__：生产与回归的检索都按 companion_id 过滤，
这条数据永远不会出现在任何业务结果里；测试结束立即删除。

用法：
    cd RAG-Knowledge-System/backend
    python -I scripts/milvus_rbac_probe.py
"""

import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymilvus import Collection, MilvusClient, connections, utility  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent.parent
ENV_FILE = BACKEND_DIR / ".env"
PW_FILE = PROJECT_ROOT / "logs" / ".milvus_rag_pw"

PROBE_COMPANION = "__rbac_probe__"
PROBE_COLLECTION = "kb_chunks"
PROBE_DIM = 2048

results: list[tuple[str, bool, str]] = []


def read_env(key: str) -> str:
    text = ENV_FILE.read_text(encoding="utf-8-sig", errors="replace")
    match = re.search(rf"^{re.escape(key)}=(.*)$", text, re.M)
    return match.group(1).strip() if match else ""


def step(name: str, fn):
    """执行一步并记录结果；异常不中断，便于一次看全所有缺口。"""
    try:
        detail = fn()
        results.append((name, True, str(detail)[:100]))
        print(f"  PASS  {name}: {detail}")
        return True
    except Exception as exc:  # noqa: BLE001
        results.append((name, False, str(exc)[:160]))
        print(f"  FAIL  {name}: {type(exc).__name__} {str(exc)[:140]}")
        return False


def main() -> int:
    user = "milvus_rag"
    password = PW_FILE.read_text(encoding="utf-8-sig").strip()
    host = read_env("MILVUS_HOST") or "127.0.0.1"
    port = int(read_env("MILVUS_PORT") or 19530)

    print(f"[probe] 以 {user} 连接 {host}:{port}")
    connections.connect(alias="probe", host=host, port=port, user=user, password=password, timeout=10)
    print("[probe] 连接成功\n")

    print("[1] 只读操作")
    step("has_collection(kb_chunks)", lambda: utility.has_collection(PROBE_COLLECTION, using="probe"))
    step("has_collection(kb_chunks_hybrid)", lambda: utility.has_collection("kb_chunks_hybrid", using="probe"))
    # list_collections 仅作信息项：8002 不使用它（知识库列表走 MySQL 的
    # app/api/v1/collections.py），且 Milvus 2.6 对非 root 用户调用会报
    # "etcdserver: invalid auth token"（服务端缺陷，与授权无关）。
    try:
        print(f"  INFO  list_collections: {sorted(utility.list_collections(using='probe'))}")
    except Exception as exc:  # noqa: BLE001
        print(f"  INFO  list_collections 不可用（8002 不使用，忽略）：{str(exc)[:80]}")

    coll = Collection(PROBE_COLLECTION, using="probe")
    step("Collection() 构造 + describe", lambda: coll.description[:40])
    step("load()", lambda: coll.load() or "loaded")
    step("num_entities", lambda: coll.num_entities)

    print("\n[2] 检索（服务端 embedding Function 需要能调智谱）")
    step(
        "search(dense)",
        lambda: [
            (round(h.score, 4), h.entity.get("vector_id"))
            for h in coll.search(
                data=["RAG 知识库的检索测试查询"],
                anns_field="dense",
                param={"metric_type": "COSINE", "params": {"ef": 64}},
                limit=2,
                output_fields=["vector_id", "collection_id"],
            )[0]
        ],
    )
    step(
        "query(expr)",
        lambda: len(coll.query(expr='collection_id != ""', output_fields=["collection_id"], limit=5)),
    )

    print("\n[3] 写操作（探针数据，结束后删除）")
    doc_id = f"rbac-probe-{uuid.uuid4().hex[:8]}"
    vector_id = f"rbac-probe-{uuid.uuid4().hex[:8]}"

    def do_insert():
        # 不走 add_chunks：探针需要显式给 companion_id，且避免触碰业务代码
        coll.insert(
            [
                {
                    "text": "RBAC 权限探针：这条数据仅用于验证 milvus_rag 的写权限，测试后立即删除。",
                    "companion_id": PROBE_COMPANION,
                    "collection_id": "rbac-probe-collection",
                    "document_id": doc_id,
                    "chunk_index": 0,
                    "vector_id": vector_id,
                }
            ]
        )
        return f"document_id={doc_id}"

    inserted = step("insert()", do_insert)
    step("flush()", lambda: coll.flush() or "flushed")

    def verify_visible():
        rows = coll.query(expr=f'document_id == "{doc_id}"', output_fields=["vector_id"])
        return f"命中 {len(rows)} 条"

    step("query(验证写入可见)", verify_visible)

    def do_delete():
        coll.delete(f'document_id == "{doc_id}"')
        coll.flush()
        return "已删除"

    deleted = step("delete() + flush()", do_delete)

    def verify_gone():
        rows = coll.query(expr=f'document_id == "{doc_id}"', output_fields=["vector_id"])
        return f"剩余 {len(rows)} 条（Milvus 逻辑删除，可能短暂可见）"

    step("query(验证删除)", verify_gone)

    print("\n[4] 高危操作必须被拒绝（最小权限验证）")
    client = MilvusClient(uri=f"http://{host}:{port}", user=user, password=password, timeout=10)

    def expect_denied(label, fn):
        try:
            fn()
            results.append((label, False, "未被拒绝——权限过大"))
            print(f"  FAIL  {label}: 未被拒绝，说明权限过大")
            return False
        except Exception as exc:  # noqa: BLE001
            results.append((label, True, "已拒绝"))
            print(f"  PASS  {label}: 已拒绝（{type(exc).__name__}）")
            return True

    expect_denied("drop_collection(禁止)", lambda: client.drop_collection(PROBE_COLLECTION))
    expect_denied("create_user(禁止)", lambda: client.create_user("rbac_should_fail", "x" * 12))
    expect_denied("create_collection(禁止)", lambda: client.create_collection("rbac_should_fail", dimension=8))
    expect_denied("list_users(禁止)", lambda: client.list_users())

    connections.disconnect("probe")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n[result] {passed}/{total} 通过")
    if not inserted or not deleted:
        print("[warn] 写入或删除失败，检查是否有残留探针数据（companion_id=__rbac_probe__）")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
