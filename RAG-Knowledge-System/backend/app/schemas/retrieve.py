"""
检索 请求/响应模型。
主服务 search_knowledge 工具调用 /api/v1/kb/retrieve 时使用同一套结构。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    # 按角色检索（推荐）：自动路由到该角色绑定的所有知识库
    companionId: Optional[str] = Field(None, max_length=36)
    # 也可直接指定知识库（检索测试页用）
    collectionIds: Optional[List[str]] = None
    query: str = Field(..., min_length=1)
    topK: Optional[int] = Field(None, ge=1, le=20)
    # 仅在 dense 模式生效（COSINE/TEI 都是 0~1 相似度）。
    # hybrid 模式（HYBRID_SEARCH_ENABLED=true）下分数是 RRF 名次融合分，本字段被忽略，
    # 由服务端 settings.hybrid_score_threshold 决定下限。
    scoreThreshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class RetrievedChunk(BaseModel):
    content: str
    score: float
    documentId: Optional[str] = None
    documentTitle: Optional[str] = None
    collectionId: Optional[str] = None
    collectionName: Optional[str] = None
    chunkIndex: Optional[int] = None


class RetrieveResponse(BaseModel):
    chunks: List[RetrievedChunk]
    elapsedMs: int
    searchedCollections: List[str] = []
    # cosine / tei：0~1 相似度；rrf：名次融合分（0.015~0.033 量级），不可当相似度解读
    scoreScale: str = "cosine"
