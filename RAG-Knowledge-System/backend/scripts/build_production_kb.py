"""为预置伴侣 preset-2（小智）建立生产知识库并导入项目文档。

背景：2026-11-24 端到端排查发现 preset-2 名下唯一知识库
a6ff8355（simple-hash 256 维）从未迁入 Milvus，检索恒空，
导致「这个项目用的技术栈是什么」在前端路径答「知识库里没有」。
本脚本建一个 Milvus 后端的生产库，绑定 preset-2。

预置伴侣禁止用户建库（api/v1/collections.py:33 allow_preset=False），
本脚本以 created_by=system 直接落库，等价于「系统级知识」，
符合 security.py:148-152 的设计意图。

切块规则完全沿用 ingest.run_ingest（不新写切块逻辑）。

用法：
    cd RAG-Knowledge-System/backend
    python scripts/build_production_kb.py --dry-run
    python scripts/build_production_kb.py --apply
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.collection import KbCollection  # noqa: E402
from app.models.document import KbDocument  # noqa: E402
from app.services.collection_service import CollectionService  # noqa: E402
from app.services.document_service import DocumentService  # noqa: E402
from app.workers.ingest import run_ingest  # noqa: E402

PROJECT_ROOT = BACKEND_DIR.parent.parent
COMPANION_ID = "preset-2"
COLLECTION_NAME = "小智的项目知识库"
CREATED_BY = "system"

# 切片数验收下限：5 篇现状文档按 500/50 切块实测 337 块，加人工事实块 1 块 = 338。
# 切块参数或文档集变更时须同步重算此值，否则自检会按旧口径误判。
EXPECTED_MIN_CHUNKS = 338

# 导入清单：只收「描述现状」的文档。
# 排除验收报告类——它们引用 tests/rag_regression/fixtures 的虚构示例答案
# （FastAPI + PostgreSQL），导入会把回归世界的事实带进生产库。
# 排除方案/排期/任务清单类——它们写的是「打算做什么」，不是现状；
# 实测 AI聊天功能优化方案一篇文章 104 块，把「技术栈」类查询的前 11 名全部占满，
# 压掉真正描述现状的块（E-2 同类稀释问题）。
DOCUMENT_FILES = [
    "01-项目架构设计文档.md",
    "03-API接口文档.md",
    "前端技术文档.md",
    "后端技术文档.md",
    "RAG知识库技术栈方案.md",
]

# 人工事实块：版本号逐条对照源码/运行环境核实（2026-11-24）。
# 刻意写成连续段落而非列表：_split_list_items 会把多个 bullet 拆成多条短块，
# 单条信息密度不足，「技术栈」查询会被长文档挤掉（实测拆成 7 块时排不进 top-20）。
# 维护义务：项目技术栈变更时必须同步更新本块，见 CLAUDE.md。
STACK_FACT = """# 本项目的技术栈

本项目采用前后端分离的四服务架构。前端使用 Vue 3.4、TypeScript、Vite 5、Pinia 和 Tailwind CSS 3.4，运行在 3000 端口。业务后端使用 Spring Boot 3.1.5 和 MyBatis Plus 3.5.5，编译目标 Java 17、运行环境 JDK 21，端口 8081，关系数据库为 MySQL，业务库名为 ai_companion。AI 服务使用 Python 3.12、FastAPI 和 LangChain 1.x，端口 5000，对接智谱 GLM 系列模型，其中 glm-4.5-air 负责文本、glm-4v-flash 负责视觉、cogview-4 负责图像、embedding-3 负责向量化。知识库服务使用 Python 3.12、FastAPI 和 Milvus 2.6 向量数据库，配合 TEI 做重排，端口 8002，元数据存放在 MySQL 的 rag_knowledge 库。本项目不使用 PostgreSQL，也不使用 Flask。缓存使用 Redis，Redis 不可用时自动降级为进程内内存缓存。
"""


def find_collection(db, name: str):
    return (
        db.query(KbCollection)
        .filter(KbCollection.name == name, KbCollection.deleted == 0)
        .first()
    )


def count_milvus(collection_id: str) -> int:
    """统计 Milvus 中该知识库的切片数（按 collection_id 过滤）。

    MilvusStore 未提供按 collection 计数的方法（`count entities with pagination`
    在 2.6 上不可用），这里用 query 拉回 collection_id 再本地计数。
    """
    from app.vectorstore.store import get_milvus_store

    store = get_milvus_store()
    collection = store._get_collection()  # noqa: SLF001 脚本侧只读查询
    expr = f'collection_id == "{collection_id}"'
    rows = collection.query(expr=expr, output_fields=["collection_id"], limit=16384)
    return len(rows)


def read_doc_state(doc_id: str):
    """用独立 session 读文档终态。

    run_ingest 自己开 session 并提交，本脚本持有的 session 读到的是旧快照；
    直接 refresh 会拿到入库前的 status，错误信息也随之丢失。
    """
    fresh = SessionLocal()
    try:
        doc = fresh.query(KbDocument).filter(KbDocument.id == doc_id).first()
        if doc is None:
            return "missing", 0, "文档记录不存在"
        return doc.status, doc.chunk_count, doc.error_msg
    finally:
        fresh.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="真正写库（默认只预演）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划")
    args = parser.parse_args()
    apply = args.apply and not args.dry_run

    if SessionLocal is None:
        print("数据库不可用，检查 .env 的 DATABASE_URL")
        return 1
    if settings.vector_store_backend.lower() != "milvus":
        print(f"当前 VECTOR_STORE_BACKEND={settings.vector_store_backend}，本脚本要求 milvus")
        return 1

    # ---- 导入清单校验 ----
    missing = [f for f in DOCUMENT_FILES if not (PROJECT_ROOT / "docs" / f).is_file()]
    if missing:
        print("缺少文档：" + ", ".join(missing))
        return 1

    print(f"目标伴侣：{COMPANION_ID}")
    print(f"知识库名：{COLLECTION_NAME}")
    print(f"向量后端：{settings.vector_store_backend} / {settings.embedding_model} / {settings.embedding_dim}")
    print(f"切块参数：chunk_size={settings.default_chunk_size} overlap={settings.default_chunk_overlap}")
    print(f"文档数：{len(DOCUMENT_FILES)} + 1 条人工事实块")
    for f in DOCUMENT_FILES:
        size = (PROJECT_ROOT / "docs" / f).stat().st_size
        print(f"  - {f} ({size} B)")
    print(f"  - [人工] 本项目的技术栈 ({len(STACK_FACT)} 字符)")

    if not apply:
        print("\n[dry-run] 未写库。加 --apply 执行。")
        return 0

    db = SessionLocal()
    try:
        coll = find_collection(db, COLLECTION_NAME)
        if coll is not None:
            print(f"\n知识库已存在 id={coll.id}，跳过创建（幂等）。")
            print("如需重建请先删除该知识库后重跑。")
            return 0

        # ---- 1. 建库 ----
        coll = KbCollection(
            name=COLLECTION_NAME,
            description="小智（preset-2）的项目知识库：项目架构、接口、前后端实现与编码约定。",
            companion_id=COMPANION_ID,
            parser_config=None,
            embedding_model=settings.embedding_model,
            embedding_dim=settings.embedding_dim,
            embedding_backend=settings.vector_store_backend.lower(),
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
            status="active",
            created_by=CREATED_BY,
        )
        db.add(coll)
        db.commit()
        db.refresh(coll)
        print(f"\n[创建] collection_id={coll.id}")

        svc = DocumentService(db)

        # ---- 2. 导入文档 ----
        for name in DOCUMENT_FILES:
            src = PROJECT_ROOT / "docs" / name
            content = src.read_bytes()
            path = DocumentService.save_upload(coll.id, name, content)
            doc = svc.create_file_doc(
                collection_id=coll.id,
                file_name=name,
                file_size=len(content),
                file_path=path,
                created_by=CREATED_BY,
            )
            doc_id = doc.id
            run_ingest(doc_id)
            status, chunk_count, error_msg = read_doc_state(doc_id)
            print(f"[入库] {name} -> {status} chunks={chunk_count}")
            if status != "completed":
                print(f"   !! 失败：{error_msg}")
                return 2

        # ---- 3. 人工事实块 ----
        fact_doc = svc.create_manual_doc(
            collection_id=coll.id,
            title="本项目的技术栈",
            content=STACK_FACT,
            created_by=CREATED_BY,
        )
        fact_id = fact_doc.id
        run_ingest(fact_id)
        status, chunk_count, error_msg = read_doc_state(fact_id)
        print(f"[入库] 人工事实块 -> {status} chunks={chunk_count}")
        if status != "completed":
            print(f"   !! 失败：{error_msg}")
            return 2

        # 计数与自检全部用独立 session。
        # 本脚本的 db 是长事务（MySQL REPEATABLE READ），run_ingest 在别的 session
        # 提交的新切片它看不到；expire_all() 不结束事务，必须换 session 才准。
        from app.models.chunk import KbChunk

        check = SessionLocal()
        try:
            CollectionService(check).refresh_counts(coll.id)
            refreshed = check.query(KbCollection).filter(KbCollection.id == coll.id).first()
            db_chunks = (
                check.query(KbChunk).filter(KbChunk.collection_id == coll.id).count()
            )
            print(
                f"\n[完成] documents={refreshed.document_count} "
                f"chunks={refreshed.chunk_count}"
            )
        finally:
            check.close()

        milvus_chunks = count_milvus(coll.id)
        print(f"[自检] kb_chunk={db_chunks}  milvus={milvus_chunks}")
        if db_chunks != milvus_chunks:
            print("   !! MySQL 与 Milvus 切片数不一致，导入不完整，请删除该库后重导")
            return 3
        if db_chunks < EXPECTED_MIN_CHUNKS:
            print(f"   !! 切片数 {db_chunks} 低于预期下限 {EXPECTED_MIN_CHUNKS}")
            return 3
        print("[自检] 通过")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
