"""
知识库集合接口。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import fail, ok
from app.db.database import get_db
from app.schemas.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
)
from app.services.collection_service import CollectionService
from app.vectorstore.store import get_vector_store

router = APIRouter()


@router.post("/collections")
async def create_collection(req: CollectionCreateRequest, db: Session = Depends(get_db)):
    """创建知识库。"""
    svc = CollectionService(db)
    coll = svc.create(req)
    return ok(coll.to_dict(), message="创建成功")


@router.get("/collections")
async def list_collections(
    keyword: str = Query(None),
    companionId: str = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """知识库列表（分页）。"""
    svc = CollectionService(db)
    rows, total = svc.list_collections(keyword, companionId, page, pageSize)
    return ok(
        {
            "items": [c.to_dict() for c in rows],
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


@router.get("/collections/{collection_id}")
async def get_collection(collection_id: str, db: Session = Depends(get_db)):
    """知识库详情。"""
    coll = CollectionService(db).get(collection_id)
    if coll is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return ok(coll.to_dict())


@router.put("/collections/{collection_id}")
async def update_collection(
    collection_id: str, req: CollectionUpdateRequest, db: Session = Depends(get_db)
):
    """更新知识库。embedding_model / embedding_dim 不可修改。"""
    svc = CollectionService(db)
    coll = svc.get(collection_id)
    if coll is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    coll = svc.update(coll, req)
    return ok(coll.to_dict(), message="更新成功")


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: str, db: Session = Depends(get_db)):
    """删除知识库（级联清理文档、切片、向量 collection）。"""
    svc = CollectionService(db)
    coll = svc.get(collection_id)
    if coll is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 先删向量（Chroma 无事务，失败也继续走元数据清理，避免脏读）
    try:
        get_vector_store().drop_collection(collection_id)
    except Exception as e:
        print(f"[collections] 删除向量 collection 失败: {e}")

    svc.delete(coll)
    return ok({"id": collection_id}, message="删除成功")
