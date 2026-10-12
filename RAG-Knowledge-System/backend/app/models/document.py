"""
知识文档 ORM 模型。

对应表 kb_document。
一条记录 = 一个上传文件 或 一条手动录入知识。
异步任务状态直接挂在本表（status / progress / task_id），不额外建任务表。
"""

import uuid

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base

# 状态机（一期 BackgroundTasks / 二期 Celery 共用）
STATUS_PENDING = "pending"
STATUS_PARSING = "parsing"
STATUS_CHUNKING = "chunking"
STATUS_EMBEDDING = "embedding"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

SOURCE_FILE = "file"
SOURCE_MANUAL = "manual"


class KbDocument(Base):
    """知识文档。"""

    __tablename__ = "kb_document"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String(36), nullable=False, index=True)

    source_type = Column(String(20), nullable=False, default=SOURCE_FILE)
    title = Column(String(255), nullable=False)

    file_name = Column(String(255), nullable=True)
    file_ext = Column(String(20), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_path = Column(String(500), nullable=True)

    raw_content = Column(Text, nullable=True)

    status = Column(String(20), nullable=False, default=STATUS_PENDING)
    progress = Column(Integer, nullable=False, default=0)
    error_msg = Column(Text, nullable=True)
    task_id = Column(String(64), nullable=True, index=True)

    chunk_count = Column(Integer, nullable=False, default=0)
    created_by = Column(String(36), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted = Column(Integer, nullable=False, default=0)

    def to_dict(self, with_content: bool = False) -> dict:
        data = {
            "id": self.id,
            "collectionId": self.collection_id,
            "sourceType": self.source_type,
            "title": self.title,
            "fileName": self.file_name,
            "fileExt": self.file_ext,
            "fileSize": self.file_size,
            "status": self.status,
            "progress": self.progress,
            "errorMsg": self.error_msg,
            "taskId": self.task_id,
            "chunkCount": self.chunk_count,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_content:
            data["rawContent"] = self.raw_content
            data["filePath"] = self.file_path
        return data
