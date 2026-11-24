"""Milvus 专用业务账号建号与授权（P2-5 动作 3，A 档精确最小权限）。

背景：8002 原以 root 超级账号连接 Milvus。本脚本建 milvus_rag 专用账号，
只授予 8002 实际用到的权限，排除 Upsert / Import / Compaction / LoadBalance /
DropIndex / CreatePartition / DropPartition / AddCollectionField 等业务用不到的项。

权限依据（逐条对应 app/vectorstore/milvus_store.py 的实际调用）：
- has_collection / Collection() 构造 → DescribeCollection
    （public 角色已对所有用户全局授予，无需重复授予）
- collection.load()                 → Load（+ GetLoadState / GetLoadingProgress）
- collection.insert()               → Insert
- collection.flush()                → Flush（+ GetFlushState）
- collection.search()/hybrid_search → Search
- collection.query()                → Query
- collection.delete()               → Delete
- collection.create_index()         → CreateIndex（仅首次建集合时需要）

用法：
    cd RAG-Knowledge-System/backend
    python -I scripts/milvus_rbac_setup.py --check   # 只读：打印现有用户/角色
    python -I scripts/milvus_rbac_setup.py --apply   # 建号+授权（幂等）

口令处理：优先读 logs/.milvus_rag_pw；不存在则生成 32 字符随机口令写回该文件。
全程只输出长度与 sha256 前 8 位，不打印明文。
"""

import argparse
import hashlib
import os
import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymilvus import MilvusClient  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent.parent
ENV_FILE = BACKEND_DIR / ".env"
PW_FILE = PROJECT_ROOT / "logs" / ".milvus_rag_pw"

ROLE_NAME = "rag_rw"
USER_NAME = "milvus_rag"
DB_NAME = "default"
COLLECTIONS = ["kb_chunks", "kb_chunks_hybrid"]

# 只读集：只保留 8002 实际调用 + load/search/flush 的服务端内部校验项。
# IndexDetail / DescribeCollection / ListAliases 已由 public 角色全局授予，不重复给；
# DescribeAlias / GetImportProgress / ListImport 8002 从不调用，删除。
COLLECTION_READ_PRIVS = [
    "Query",              # collection.query()（build_production_kb 计数）
    "Search",             # collection.search() / hybrid_search()
    "GetFlushState",      # flush 状态查询
    "GetLoadState",       # load 内部校验
    "GetLoadingProgress", # load 内部校验
    "HasPartition",       # partition key 集合内部校验
    "ShowPartitions",     # partition 元数据
    "GetStatistics",      # num_entities / 统计
]

# 写集：只挑业务链路真正用到的 5 项。
# Release 8002 从不调用，删除；CreateIndex 保留——集合存在但索引缺失时是唯一自愈手段。
COLLECTION_WRITE_PRIVS = [
    "Load",
    "Insert",
    "Delete",
    "Flush",
    "CreateIndex",
]

# 数据库级授权：空。
# Milvus 的 ObjectType 只有 Collection / Global / User，没有 Database——原计划授
# ShowCollections / DescribeDatabase 时报 "the object entity in the request is nil or invalid"。
# 改用 Global 授上又实测无效：milvus_rag 调 list_collections 报
# "etcdserver: invalid auth token"（Milvus 2.6 非 root 用户服务端缺陷，与授权无关）。
# 8002 不调用 list_collections（知识库列表走 MySQL），故已于 2026-11-24 全部撤销。
DATABASE_PRIVS: list[str] = []

# 明确不授予（仅用于报告核对，不参与授权）
EXCLUDED_PRIVS = [
    "Upsert",
    "Import",
    "Compaction",
    "LoadBalance",
    "DropIndex",
    "CreatePartition",
    "DropPartition",
    "AddCollectionField",
    "DropCollection",
    "RenameCollection",
    "CreateAlias",
    "DropAlias",
    "FlushAll",
    "TruncateCollection",
    "CreateDatabase",
    "DropDatabase",
    "BackupRBAC",
    "RestoreRBAC",
    "CreateUser",
    "UpdateUser",
    "CreateRole",
    "OperatePrivilege",
]


def fingerprint(secret: str) -> str:
    """长度 + sha256 前 8 位，用于不暴露明文的核对。"""
    return f"len={len(secret)} sha8={hashlib.sha256(secret.encode()).hexdigest()[:8]}"


def read_env(key: str) -> str:
    text = ENV_FILE.read_text(encoding="utf-8-sig", errors="replace")
    match = re.search(rf"^{re.escape(key)}=(.*)$", text, re.M)
    return match.group(1).strip() if match else ""


def load_or_create_password() -> tuple[str, bool]:
    """读取或生成 milvus_rag 口令；返回 (口令, 是否新生成)。"""
    if PW_FILE.is_file():
        value = PW_FILE.read_text(encoding="utf-8-sig").strip()
        if value:
            return value, False
    value = secrets.token_urlsafe(24)  # 32 字符，含大小写/数字/-/_，无引号空格
    PW_FILE.parent.mkdir(parents=True, exist_ok=True)
    PW_FILE.write_text(value, encoding="utf-8")
    return value, True


def admin_client(timeout: float = 15.0) -> MilvusClient:
    """用 root 凭据建管理连接（明文不出函数）。

    注意：`RAG-Knowledge-System/backend/.env` 的 MILVUS_USER 已切为 milvus_rag
    （8002 业务账号），它没有建号/授权权限，不能用于管理操作。root 口令优先读
    `logs/.milvus_root_pw`（轮换后的当前值），不存在才回落到 .env（仅当 .env 还是 root 时有效）。
    """
    root_pw_file = PROJECT_ROOT / "logs" / ".milvus_root_pw"
    if root_pw_file.is_file():
        user, password = "root", root_pw_file.read_text(encoding="utf-8-sig").strip()
    else:
        user, password = read_env("MILVUS_USER"), read_env("MILVUS_PASSWORD")
        if user != "root":
            raise SystemExit(
                "管理连接需要 root 凭据：请先创建 logs/.milvus_root_pw（见 deploy/milvus/ops.local.md）"
            )
    return MilvusClient(
        uri=f"http://{read_env('MILVUS_HOST') or '127.0.0.1'}:{read_env('MILVUS_PORT') or '19530'}",
        user=user,
        password=password,
        timeout=timeout,
    )


def do_check(client: MilvusClient) -> None:
    print("[check] users:", sorted(client.list_users()))
    roles = client.list_roles()
    names = [r.get("role") if isinstance(r, dict) else str(r) for r in roles]
    print("[check] roles:", sorted(names))
    if ROLE_NAME in names:
        print(f"[check] {ROLE_NAME} 权限：")
        for item in client.describe_role(ROLE_NAME).get("privileges", []):
            print(
                "   ",
                item.get("object_type"),
                "|",
                item.get("privilege"),
                "|",
                item.get("object_name"),
            )
    else:
        print(f"[check] 角色 {ROLE_NAME} 尚未创建")


def ensure_user(client: MilvusClient, password: str) -> None:
    users = client.list_users()
    if USER_NAME in users:
        print(f"[apply] 用户 {USER_NAME} 已存在，跳过创建")
        return
    client.create_user(USER_NAME, password, description="RAG 8002 专用业务账号")
    print(f"[apply] 用户 {USER_NAME} 创建成功（{fingerprint(password)}）")


def ensure_role(client: MilvusClient) -> None:
    roles = [r.get("role") if isinstance(r, dict) else str(r) for r in client.list_roles()]
    if ROLE_NAME in roles:
        print(f"[apply] 角色 {ROLE_NAME} 已存在，跳过创建")
        return
    client.create_role(ROLE_NAME, description="8002 最小权限：读写 kb_chunks 两集合")
    print(f"[apply] 角色 {ROLE_NAME} 创建成功")


def grant_all(client: MilvusClient) -> list[str]:
    """逐条授权，返回失败项列表（不中断，便于一次看全）。"""
    failures: list[str] = []

    for priv in DATABASE_PRIVS:
        try:
            client.grant_privilege(ROLE_NAME, "Global", priv, "*", DB_NAME)
            print(f"[grant] Global {priv}: OK")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"Global {priv}: {exc}")
            print(f"[grant] Global {priv}: FAIL {exc}")

    for coll in COLLECTIONS:
        for priv in COLLECTION_READ_PRIVS + COLLECTION_WRITE_PRIVS:
            try:
                client.grant_privilege(ROLE_NAME, "Collection", priv, coll, DB_NAME)
                print(f"[grant] Collection {priv} on {coll}: OK")
            except Exception as exc:  # noqa: BLE001
                failures.append(f"Collection {priv} on {coll}: {exc}")
                print(f"[grant] Collection {priv} on {coll}: FAIL {exc}")

    return failures


def bind_user(client: MilvusClient) -> None:
    # describe_role 在 pymilvus 3.0.2 不含 users 字段，无法回读绑定关系；
    # 重复 grant_role 是幂等的，直接执行即可。
    client.grant_role(USER_NAME, ROLE_NAME)
    print(f"[apply] {USER_NAME} 已绑定角色 {ROLE_NAME}（幂等）")


def report(client: MilvusClient) -> None:
    privileges = client.describe_role(ROLE_NAME).get("privileges", [])
    print(f"\n[report] {ROLE_NAME} 实际权限 {len(privileges)} 条：")
    for item in sorted(
        privileges, key=lambda x: (x.get("object_type", ""), x.get("object_name", ""), x.get("privilege", ""))
    ):
        print(f"   {item.get('object_type'):<10} {item.get('privilege'):<22} {item.get('object_name')}")

    granted = {item.get("privilege") for item in privileges}
    leaked = sorted(granted & set(EXCLUDED_PRIVS))
    print(f"[report] 高危权限泄漏检查：{'无' if not leaked else leaked}")
    print(f"[report] 用户：{sorted(client.list_users())}")


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="只读：打印现有用户/角色/权限")
    action.add_argument("--apply", action="store_true", help="建号 + 授权（幂等）")
    args = parser.parse_args()

    client = admin_client()
    if args.check:
        do_check(client)
        return 0

    password, created = load_or_create_password()
    print(f"[apply] {USER_NAME} 口令：{fingerprint(password)}（{'新生成' if created else '沿用'} {PW_FILE.name}）")

    ensure_user(client, password)
    ensure_role(client)
    failures = grant_all(client)
    bind_user(client)
    report(client)

    if failures:
        print(f"\n[result] 有 {len(failures)} 条授权失败：")
        for item in failures:
            print("   -", item)
        return 1

    print("\n[result] 全部授权成功")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
