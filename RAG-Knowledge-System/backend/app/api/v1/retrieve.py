"""
检索接口。
主服务的 search_knowledge 工具与前端"检索测试"页共用本接口。
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import ok
from app.db.database import get_db
from app.schemas.retrieve import RetrieveRequest
from app.services.collection_service import CollectionService
from app.vectorstore.store import get_chroma_store

router = APIRouter()


@router.post("/retrieve")
async def retrieve(req: RetrieveRequest, db: Session = Depends(get_db)):
    """按角色或按知识库检索。

    路由规则：
    - 传了 collectionIds -> 直接检索这些库；
    - 只传 companionId  -> 查该角色绑定的所有 active 知识库；
    - 两者都没传        -> 400。
    """
    started = time.perf_counter()
    svc = CollectionService(db)

    collections = []
    if req.collectionIds:
        for cid in req.collectionIds:
            coll = svc.get(cid)
            if coll is not None:
                collections.append(coll)
    elif req.companionId:
        collections = svc.list_by_companion(req.companionId)
    else:
        raise HTTPException(status_code=400, detail="必须提供 companionId 或 collectionIds")

    if not collections:
        return ok({"chunks": [], "elapsedMs": 0, "searchedCollections": []}, message="没有可检索的知识库")

    coll_map = {c.id: c for c in collections}
    coll_ids = list(coll_map.keys())

    top_k = req.topK or settings.retrieve_top_k
    threshold = (
        req.scoreThreshold
        if req.scoreThreshold is not None
        else settings.retrieve_score_threshold
    )

    pairs = get_chroma_store().search(coll_ids, req.query, k=top_k)

    chunks = []
    for doc, score in pairs:
        if score < threshold:
            continue
        meta = doc.metadata or {}
        cid = meta.get("collection_id")
        coll = coll_map.get(cid)
        chunks.append(
            {
                "content": doc.page_content,
                "score": round(float(score), 4),
                "documentId": meta.get("document_id"),
                "documentTitle": meta.get("document_title"),
                "collectionId": cid,
                "collectionName": coll.name if coll else None,
                "chunkIndex": meta.get("chunk_index"),
            }
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ok(
        {
            "chunks": chunks,
            "elapsedMs": elapsed_ms,
            "searchedCollections": coll_ids,
        },
        message="检索完成",
    )
