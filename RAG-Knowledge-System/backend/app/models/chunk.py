"""
知识切片 ORM 模型。

对应表 kb_chunk。
每个切片对应 Chroma 中的一个向量（vector_id），删除时按 vector_id 精确清理。
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class KbChunk(Base):
    """知识切片。"""

    __tablename__ = "kb_chunk"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=False, index=True)
    collection_id = Column(String(36), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False, default=0)

    # Chroma 中的向量 id，约定为 "{document_id}::chunk_{index}"
    vector_id = Column(String(128), nullable=False)

    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "documentId": self.document_id,
            "collectionId": self.collection_id,
            "chunkIndex": self.chunk_index,
            "content": self.content,
            "charCount": self.char_count,
            "vectorId": self.vector_id,
            "meta": self.meta,
        }
