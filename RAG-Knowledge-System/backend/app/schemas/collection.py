"""
知识库集合 请求/响应模型。
字段命名沿用主服务风格（请求体使用 camelCase）。
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ParserConfig(BaseModel):
    """JSON 文件的解析规则。"""

    itemsPath: Optional[str] = Field(None, description="指向数组/对象的点号路径，如 data.list")
    contentField: str = Field("content", description="内容字段路径")
    titleField: Optional[str] = Field(None, description="标题字段路径")
    metaFields: Optional[list] = Field(default_factory=list, description="额外保留的元数据字段")


class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    companionId: Optional[str] = Field(None, max_length=36, description="绑定的 AI 伴侣 ID")
    parserConfig: Optional[ParserConfig] = None
    chunkSize: Optional[int] = Field(None, ge=50, le=2000)
    chunkOverlap: Optional[int] = Field(None, ge=0, le=500)


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    companionId: Optional[str] = Field(None, max_length=36)
    parserConfig: Optional[ParserConfig] = None
    chunkSize: Optional[int] = Field(None, ge=50, le=2000)
    chunkOverlap: Optional[int] = Field(None, ge=0, le=500)
    status: Optional[str] = Field(None, description="active / disabled")


class CollectionQuery(BaseModel):
    keyword: Optional[str] = None
    companionId: Optional[str] = None
    page: int = 1
    pageSize: int = 20


class CollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    companionId: Optional[str] = None
    parserConfig: Optional[Dict[str, Any]] = None
    embeddingModel: str
    embeddingDim: int
    embeddingBackend: str
    chunkSize: int
    chunkOverlap: int
    documentCount: int
    chunkCount: int
    status: str
    createdBy: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
