"""
知识库集合业务逻辑。
"""

from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chunk import KbChunk
from app.models.collection import KbCollection
from app.models.document import KbDocument
from app.schemas.collection import CollectionCreateRequest, CollectionUpdateRequest


class CollectionService:
    """知识库集合 CRUD。"""

    def __init__(self, db: Session):
        self.db = db

    # ---------- 查询 ----------
    def list_collections(
        self,
        keyword: Optional[str] = None,
        companion_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[KbCollection], int]:
        q = self.db.query(KbCollection).filter(KbCollection.deleted == 0)

        if keyword:
            like = f"%{keyword}%"
            q = q.filter(
                or_(KbCollection.name.ilike(like), KbCollection.description.ilike(like))
            )
        if companion_id:
            q = q.filter(KbCollection.companion_id == companion_id)

        total = q.count()
        rows = (
            q.order_by(KbCollection.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return rows, total

    def get(self, collection_id: str) -> Optional[KbCollection]:
        return (
            self.db.query(KbCollection)
            .filter(KbCollection.id == collection_id, KbCollection.deleted == 0)
            .first()
        )

    def list_by_companion(self, companion_id: str) -> List[KbCollection]:
        """按角色取所有启用的知识库（检索路由用）。"""
        return (
            self.db.query(KbCollection)
            .filter(
                KbCollection.companion_id == companion_id,
                KbCollection.deleted == 0,
                KbCollection.status == "active",
            )
            .all()
        )

    # ---------- 写入 ----------
    def create(self, req: CollectionCreateRequest, created_by: Optional[str] = None) -> KbCollection:
        use_milvus = settings.vector_store_backend.lower() == "milvus"
        coll = KbCollection(
            name=req.name,
            description=req.description,
            companion_id=req.companionId,
            parser_config=req.parserConfig.model_dump() if req.parserConfig else None,
            embedding_model=settings.embedding_model if use_milvus else "simple-hash",
            embedding_dim=settings.embedding_dim if use_milvus else 256,
            embedding_backend=settings.vector_store_backend.lower(),
            chunk_size=req.chunkSize or settings.default_chunk_size,
            chunk_overlap=req.chunkOverlap or settings.default_chunk_overlap,
            status="active",
            created_by=created_by,
        )
        self.db.add(coll)
        self.db.commit()
        self.db.refresh(coll)
        return coll

    def update(self, coll: KbCollection, req: CollectionUpdateRequest) -> KbCollection:
        """更新。embedding_* 不可改，避免维度污染。"""
        if req.name is not None:
            coll.name = req.name
        if req.description is not None:
            coll.description = req.description
        if req.companionId is not None:
            coll.companion_id = req.companionId or None
        if req.parserConfig is not None:
            coll.parser_config = req.parserConfig.model_dump()
        if req.chunkSize is not None:
            coll.chunk_size = req.chunkSize
        if req.chunkOverlap is not None:
            coll.chunk_overlap = req.chunkOverlap
        if req.status is not None:
            coll.status = req.status

        self.db.commit()
        self.db.refresh(coll)
        return coll

    def delete(self, coll: KbCollection) -> None:
        """逻辑删除集合，物理清理文档/切片（向量由路由层负责删）。"""
        self.db.query(KbDocument).filter(
            KbDocument.collection_id == coll.id, KbDocument.deleted == 0
        ).update({"deleted": 1}, synchronize_session=False)

        self.db.query(KbChunk).filter(KbChunk.collection_id == coll.id).delete(
            synchronize_session=False
        )

        coll.deleted = 1
        coll.document_count = 0
        coll.chunk_count = 0
        self.db.commit()

    # ---------- 统计 ----------
    def refresh_counts(self, collection_id: str) -> None:
        """重算集合的文档数 / 切片数。"""
        doc_count = (
            self.db.query(func.count(KbDocument.id))
            .filter(KbDocument.collection_id == collection_id, KbDocument.deleted == 0)
            .scalar()
            or 0
        )
        chunk_count = (
            self.db.query(func.count(KbChunk.id))
            .filter(KbChunk.collection_id == collection_id)
            .scalar()
            or 0
        )
        self.db.query(KbCollection).filter(KbCollection.id == collection_id).update(
            {"document_count": doc_count, "chunk_count": chunk_count},
            synchronize_session=False,
        )
        self.db.commit()
