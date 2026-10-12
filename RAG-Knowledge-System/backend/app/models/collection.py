"""
知识库集合 ORM 模型。

对应表 kb_collection。
注意：embedding_model / embedding_dim / embedding_backend 一旦写入即视为不可变，
     变更会导致同一 Chroma collection 内向量维度冲突。
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class KbCollection(Base):
    """知识库集合。"""

    __tablename__ = "kb_collection"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 跨服务引用主库 companion.id（preset-1 / UUID 字符串），不设外键
    companion_id = Column(String(36), nullable=True, index=True)

    # JSON 解析规则：{"itemsPath": "data.list", "contentField": "text", "titleField": "title"}
    parser_config = Column(JSON, nullable=True)

    # 向量配置（不可变）
    embedding_model = Column(String(50), nullable=False, default="simple-hash")
    embedding_dim = Column(Integer, nullable=False, default=256)
    embedding_backend = Column(String(20), nullable=False, default="hash")

    chunk_size = Column(Integer, nullable=False, default=500)
    chunk_overlap = Column(Integer, nullable=False, default=50)

    document_count = Column(Integer, nullable=False, default=0)
    chunk_count = Column(Integer, nullable=False, default=0)

    status = Column(String(20), nullable=False, default="active")
    created_by = Column(String(36), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted = Column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        """序列化为前端友好的 camelCase 字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "companionId": self.companion_id,
            "parserConfig": self.parser_config,
            "embeddingModel": self.embedding_model,
            "embeddingDim": self.embedding_dim,
            "embeddingBackend": self.embedding_backend,
            "chunkSize": self.chunk_size,
            "chunkOverlap": self.chunk_overlap,
            "documentCount": self.document_count,
            "chunkCount": self.chunk_count,
            "status": self.status,
            "createdBy": self.created_by,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
