"""
知识文档业务逻辑。
负责落盘、元数据维护、切片持久化；向量写入交给 workers.ingest。
"""

import os
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import KbChunk
from app.models.document import (
    SOURCE_FILE,
    SOURCE_MANUAL,
    STATUS_PENDING,
    KbDocument,
)


class DocumentService:
    """文档 CRUD。"""

    def __init__(self, db: Session):
        self.db = db

    # ---------- 查询 ----------
    def list_by_collection(
        self, collection_id: str, status: Optional[str] = None
    ) -> List[KbDocument]:
        q = self.db.query(KbDocument).filter(
            KbDocument.collection_id == collection_id, KbDocument.deleted == 0
        )
        if status:
            q = q.filter(KbDocument.status == status)
        return q.order_by(KbDocument.created_at.desc()).all()

    def get(self, doc_id: str) -> Optional[KbDocument]:
        return (
            self.db.query(KbDocument)
            .filter(KbDocument.id == doc_id, KbDocument.deleted == 0)
            .first()
        )

    def list_by_ids(self, doc_ids: List[Optional[str]]) -> List[KbDocument]:
        """批量取检索命中的文档标题；过滤空值与已删除文档。"""
        ids = [doc_id for doc_id in doc_ids if doc_id]
        if not ids:
            return []
        return (
            self.db.query(KbDocument)
            .filter(KbDocument.id.in_(ids), KbDocument.deleted == 0)
            .all()
        )

    def list_chunks(self, doc_id: str) -> List[KbChunk]:
        return (
            self.db.query(KbChunk)
            .filter(KbChunk.document_id == doc_id)
            .order_by(KbChunk.chunk_index.asc())
            .all()
        )

    # ---------- 落盘 ----------
    @staticmethod
    def save_upload(collection_id: str, file_name: str, content: bytes) -> str:
        """把上传文件写入 storage/uploads/{collection_id}/{uuid}.{ext}。

        Returns:
            绝对路径。
        """
        ext = (os.path.splitext(file_name)[1] or "").lstrip(".").lower()
        target_dir = os.path.abspath(
            os.path.join(settings.upload_dir, collection_id)
        )
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, f"{uuid.uuid4().hex}.{ext}")
        with open(target, "wb") as f:
            f.write(content)
        return target

    # ---------- 创建 ----------
    def create_file_doc(
        self,
        collection_id: str,
        file_name: str,
        file_size: int,
        file_path: str,
        title: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> KbDocument:
        ext = (os.path.splitext(file_name)[1] or "").lstrip(".").lower()
        doc = KbDocument(
            collection_id=collection_id,
            source_type=SOURCE_FILE,
            title=title or os.path.splitext(os.path.basename(file_name))[0],
            file_name=file_name,
            file_ext=ext,
            file_size=file_size,
            file_path=file_path,
            status=STATUS_PENDING,
            progress=0,
            created_by=created_by,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def create_manual_doc(
        self,
        collection_id: str,
        title: str,
        content: str,
        created_by: Optional[str] = None,
    ) -> KbDocument:
        doc = KbDocument(
            collection_id=collection_id,
            source_type=SOURCE_MANUAL,
            title=title,
            raw_content=content,
            status=STATUS_PENDING,
            progress=0,
            created_by=created_by,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # ---------- 更新 ----------
    def update_manual_doc(self, doc: KbDocument, title: Optional[str], content: Optional[str]) -> KbDocument:
        if title is not None:
            doc.title = title
        if content is not None:
            doc.raw_content = content
        # 重新回到待处理，由调用方重新投递任务
        doc.status = STATUS_PENDING
        doc.progress = 0
        doc.error_msg = None
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def mark_task(self, doc: KbDocument, task_id: str) -> KbDocument:
        doc.task_id = task_id
        self.db.commit()
        self.db.refresh(doc)
        return doc

    # ---------- 删除 ----------
    def prepare_delete(self, doc: KbDocument) -> List[str]:
        """逻辑删除文档 + 物理删除切片记录，返回待清理的向量 id 列表。"""
        vector_ids = [
            row.vector_id
            for row in self.db.query(KbChunk)
            .filter(KbChunk.document_id == doc.id)
            .all()
        ]
        self.db.query(KbChunk).filter(KbChunk.document_id == doc.id).delete(
            synchronize_session=False
        )
        doc.deleted = 1
        self.db.commit()
        return vector_ids

    def reset_for_reindex(self, doc: KbDocument) -> List[str]:
        """重建索引前清空旧切片，返回待清理的向量 id 列表。"""
        vector_ids = [
            row.vector_id
            for row in self.db.query(KbChunk)
            .filter(KbChunk.document_id == doc.id)
            .all()
        ]
        self.db.query(KbChunk).filter(KbChunk.document_id == doc.id).delete(
            synchronize_session=False
        )
        doc.status = STATUS_PENDING
        doc.progress = 0
        doc.error_msg = None
        doc.chunk_count = 0
        self.db.commit()
        return vector_ids

    def save_chunks(self, doc: KbDocument, chunks: List[dict]) -> None:
        """批量写入切片记录。chunks: [{chunk_index, content, vector_id, meta}]"""
        for c in chunks:
            self.db.add(
                KbChunk(
                    document_id=doc.id,
                    collection_id=doc.collection_id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    char_count=len(c["content"]),
                    vector_id=c["vector_id"],
                    meta=c.get("meta"),
                )
            )
        doc.chunk_count = len(chunks)
        self.db.commit()
