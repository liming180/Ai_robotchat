"""
知识文档 请求/响应模型。
"""

from typing import Optional

from pydantic import BaseModel, Field


class ManualDocumentCreateRequest(BaseModel):
    """手动录入知识。"""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    # 可选：把这条知识归属到某个角色（覆盖集合的 companionId）
    companionId: Optional[str] = None


class DocumentUpdateRequest(BaseModel):
    """编辑手动知识（会触发重新向量化）。"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    collectionId: str
    sourceType: str
    title: str
    fileName: Optional[str] = None
    fileExt: Optional[str] = None
    fileSize: Optional[int] = None
    status: str
    progress: int
    errorMsg: Optional[str] = None
    taskId: Optional[str] = None
    chunkCount: int
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class DocumentDetailResponse(DocumentResponse):
    rawContent: Optional[str] = None
    filePath: Optional[str] = None
    chunks: Optional[list] = None


class UploadResultItem(BaseModel):
    documentId: str
    taskId: str
    title: str
    fileName: Optional[str] = None


class TaskStatusResponse(BaseModel):
    taskId: str
    documentId: str
    status: str
    progress: int
    errorMsg: Optional[str] = None
    chunkCount: int = 0
