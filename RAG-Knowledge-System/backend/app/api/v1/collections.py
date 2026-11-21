"""
知识库集合接口（2026-11-21 鉴权强制化：全部要求 JWT + 归属校验）。
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.security import (
    require_collection_owner,
    require_companion_owner,
    verify_jwt,
)
from app.db.database import get_db
from app.schemas.collection import (
    CollectionCreateRequest,
    CollectionUpdateRequest,
)
from app.services.collection_service import CollectionService
from app.vectorstore.store import get_vector_store

router = APIRouter()


@router.post("/collections", dependencies=[Depends(verify_jwt)])
def create_collection(
    req: CollectionCreateRequest,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """创建知识库。绑定的伴侣必须属于本人；预置伴侣不允许（见 security.py 说明）。"""
    # allow_preset=False：预置伴侣仅允许系统级知识，避免私有库进入全员检索范围
    require_companion_owner(user_id, req.companionId, allow_preset=False)
    svc = CollectionService(db)
    coll = svc.create(req, created_by=user_id)
    return ok(coll.to_dict(), message="创建成功")


@router.get("/collections", dependencies=[Depends(verify_jwt)])
def list_collections(
    keyword: str = Query(None),
    companionId: str = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """知识库列表（只返回本人创建的知识库）。"""
    if companionId:
        # 指定伴侣时先校验归属，避免用列表接口探测他人伴侣
        require_companion_owner(user_id, companionId)
    svc = CollectionService(db)
    rows, total = svc.list_collections(keyword, companionId, page, pageSize, owner_id=user_id)
    return ok(
        {
            "items": [c.to_dict() for c in rows],
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


@router.get("/collections/{collection_id}", dependencies=[Depends(verify_jwt)])
def get_collection(
    collection_id: str,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """知识库详情（仅本人）。"""
    coll = require_collection_owner(user_id, collection_id)
    return ok(coll.to_dict())


@router.put("/collections/{collection_id}", dependencies=[Depends(verify_jwt)])
def update_collection(
    collection_id: str,
    req: CollectionUpdateRequest,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """更新知识库（仅本人）。embedding_model / embedding_dim 不可修改。"""
    require_collection_owner(user_id, collection_id)
    if req.companionId is not None:
        # 改绑伴侣时校验新归属，且同样禁止绑到预置伴侣
        require_companion_owner(user_id, req.companionId, allow_preset=False)

    svc = CollectionService(db)
    coll = svc.get(collection_id)
    if coll is None:
        raise HTTPException(status_code=403, detail="无权访问该资源")
    coll = svc.update(coll, req)
    return ok(coll.to_dict(), message="更新成功")


@router.delete("/collections/{collection_id}", dependencies=[Depends(verify_jwt)])
def delete_collection(
    collection_id: str,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """删除知识库（仅本人；级联清理文档、切片、向量）。"""
    require_collection_owner(user_id, collection_id)

    svc = CollectionService(db)
    coll = svc.get(collection_id)
    if coll is None:
        raise HTTPException(status_code=403, detail="无权访问该资源")

    # 先删向量（失败也继续走元数据清理，避免脏读）
    try:
        get_vector_store().drop_collection(collection_id)
    except Exception as e:
        print(f"[collections] 删除向量 collection 失败: {e}")

    svc.delete(coll)
    return ok({"id": collection_id}, message="删除成功")
