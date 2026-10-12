"""
文档入库流水线：解析 → 切片 → 向量化 → 写入 Chroma → 回写元数据。

一期用 FastAPI BackgroundTasks 直接调用 run_ingest(doc_id)；
二期换 Celery 时，只需把本函数包装成 @celery_app.task，
路由层的 submit_ingest 改为 ingest_document.delay(doc_id) 即可，业务代码零改动。

设计约束：
- 绝不做 Embedding 降级。向量化失败 → 文档置 failed，不写脏数据；
- 每次状态变更都 commit，前端可轮询到中间态；
- 函数内自建 DB Session，不依赖请求上下文（便于迁移到 Celery）。
"""

import traceback
import uuid
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.db.database import SessionLocal
from app.models.collection import KbCollection
from app.models.document import (
    SOURCE_MANUAL,
    STATUS_CHUNKING,
    STATUS_COMPLETED,
    STATUS_EMBEDDING,
    STATUS_FAILED,
    STATUS_PARSING,
    KbDocument,
)
from app.parsers import get_parser
from app.vectorstore.store import get_chroma_store


def new_task_id() -> str:
    """生成任务 ID（一期本地 UUID；二期可直接用 Celery 的 task id）。"""
    return uuid.uuid4().hex


# ------------------------------------------------------------------
# 状态更新辅助
# ------------------------------------------------------------------
def _set_status(db, doc: KbDocument, status: str, progress: int, error: Optional[str] = None):
    doc.status = status
    doc.progress = progress
    doc.error_msg = error
    db.commit()


# ------------------------------------------------------------------
# 各阶段
# ------------------------------------------------------------------
def _read_raw(doc: KbDocument) -> str:
    """取原始文本：手动录入直接读库，文件读磁盘。"""
    if doc.source_type == SOURCE_MANUAL:
        return doc.raw_content or ""

    if not doc.file_path:
        raise ValueError("文件路径为空，无法读取")

    with open(doc.file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _parse(doc: KbDocument, coll: KbCollection) -> list:
    raw = _read_raw(doc)
    if not raw.strip():
        raise ValueError("文件内容为空或无法解码")

    parser = get_parser(doc.file_ext or "txt")
    if parser is None:
        raise ValueError(f"不支持的文件格式: {doc.file_ext}")

    items = parser.parse(
        raw,
        default_title=doc.title,
        parser_config=coll.parser_config,
    )
    if not items:
        raise ValueError("解析后没有任何有效内容")
    return items


def _chunk(items: list, coll: KbCollection) -> List[dict]:
    """把若干条知识切成统一粒度的切片。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=coll.chunk_size,
        chunk_overlap=coll.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )

    chunks: List[dict] = []
    for item in items:
        pieces = splitter.split_text(item.content) or []
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            chunks.append(
                {
                    "title": item.title,
                    "content": piece,
                    "item_meta": item.meta or {},
                }
            )
    return chunks


# ------------------------------------------------------------------
# 主流程
# ------------------------------------------------------------------
def run_ingest(doc_id: str) -> None:
    """执行完整入库流程。异常一律吞掉并写回 error_msg，绝不向外抛。"""
    if SessionLocal is None:
        print(f"[ingest] 数据库不可用，跳过 doc={doc_id}")
        return

    db = SessionLocal()
    try:
        doc = (
            db.query(KbDocument)
            .filter(KbDocument.id == doc_id, KbDocument.deleted == 0)
            .first()
        )
        if doc is None:
            print(f"[ingest] 文档不存在或已删除: {doc_id}")
            return

        coll = (
            db.query(KbCollection)
            .filter(KbCollection.id == doc.collection_id, KbCollection.deleted == 0)
            .first()
        )
        if coll is None:
            _set_status(db, doc, STATUS_FAILED, 0, "所属知识库不存在或已删除")
            return

        # ---- 1. 解析 ----
        _set_status(db, doc, STATUS_PARSING, 10)
        items = _parse(doc, coll)

        # ---- 2. 切片 ----
        _set_status(db, doc, STATUS_CHUNKING, 30)
        chunks = _chunk(items, coll)
        if not chunks:
            _set_status(db, doc, STATUS_FAILED, 30, "切片后没有有效内容")
            return

        # ---- 3. 向量化 + 写入 Chroma ----
        _set_status(db, doc, STATUS_EMBEDDING, 50)

        chunk_ids = [f"{doc.id}::chunk_{i}" for i in range(len(chunks))]
        texts = [c["content"] for c in chunks]
        metadatas = []
        for i, c in enumerate(chunks):
            meta = {
                "collection_id": coll.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "chunk_index": i,
                "source_type": doc.source_type,
            }
            if coll.companion_id:
                meta["companion_id"] = coll.companion_id
            # Chroma metadata 只接受标量
            for k, v in (c.get("item_meta") or {}).items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
            metadatas.append(meta)

        store = get_chroma_store()
        store.add_chunks(coll.id, chunk_ids, texts, metadatas)

        # ---- 4. 回写切片元数据 ----
        from app.services.document_service import DocumentService

        DocumentService(db).save_chunks(
            doc,
            [
                {
                    "chunk_index": i,
                    "content": chunks[i]["content"],
                    "vector_id": chunk_ids[i],
                    "meta": {"title": chunks[i]["title"]},
                }
                for i in range(len(chunks))
            ],
        )

        # ---- 5. 完成 ----
        _set_status(db, doc, STATUS_COMPLETED, 100)
        from app.services.collection_service import CollectionService

        CollectionService(db).refresh_counts(coll.id)
        print(f"[ingest] 完成 doc={doc.id} chunks={len(chunks)}")

    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:500]}"
        print(f"[ingest] 失败 doc={doc_id} -> {err}")
        traceback.print_exc()
        try:
            doc = db.query(KbDocument).filter(KbDocument.id == doc_id).first()
            if doc is not None:
                _set_status(db, doc, STATUS_FAILED, doc.progress or 0, err)
        except Exception:
            pass
    finally:
        db.close()


def submit_ingest(background_tasks, doc_id: str) -> str:
    """投递入库任务，返回 task_id。

    一期：BackgroundTasks 同步排队（进程内执行）。
    二期：改为 ingest_document.delay(doc_id) 并返回 Celery task id。
    """
    task_id = new_task_id()
    background_tasks.add_task(run_ingest, doc_id)
    return task_id
