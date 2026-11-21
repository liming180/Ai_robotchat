"""
知识文档接口：上传 / 手动录入 / 列表 / 详情 / 编辑 / 删除 / 重建索引 / 任务进度。
"""

import os

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import ok
from app.core.security import (
    require_collection_owner,
    require_document_owner,
    verify_jwt,
)
from app.db.database import get_db
from app.models.document import KbDocument
from app.schemas.document import ManualDocumentCreateRequest, DocumentUpdateRequest
from app.services.collection_service import CollectionService
from app.services.document_service import DocumentService
from app.vectorstore.store import get_vector_store
from app.workers.ingest import submit_ingest

router = APIRouter()


def _require_collection(db: Session, collection_id: str):
    coll = CollectionService(db).get(collection_id)
    if coll is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return coll


def _require_document(db: Session, doc_id: str) -> KbDocument:
    doc = DocumentService(db).get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


# ------------------------------------------------------------------
# 上传文件
# ------------------------------------------------------------------
@router.post("/collections/{collection_id}/documents/upload", dependencies=[Depends(verify_jwt)])
async def upload_documents(
    collection_id: str,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """上传 json / md / txt 文件，异步解析入库（仅知识库所有者）。"""
    require_collection_owner(user_id, collection_id)
    coll = _require_collection(db, collection_id)
    svc = DocumentService(db)

    allowed = settings.allowed_extensions_list
    results = []

    for uf in files:
        file_name = uf.filename or "unnamed"
        ext = (os.path.splitext(file_name)[1] or "").lstrip(".").lower()

        if ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {ext or '(无扩展名)'}，仅支持 {allowed}",
            )

        content = await uf.read()
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"{file_name} 超过大小限制 {settings.max_file_size_mb}MB",
            )
        if not content:
            raise HTTPException(status_code=400, detail=f"{file_name} 内容为空")

        file_path = svc.save_upload(collection_id, file_name, content)
        doc = svc.create_file_doc(
            collection_id=collection_id,
            file_name=file_name,
            file_size=len(content),
            file_path=file_path,
        )
        task_id = submit_ingest(background_tasks, doc.id)
        svc.mark_task(doc, task_id)

        results.append(
            {
                "documentId": doc.id,
                "taskId": task_id,
                "title": doc.title,
                "fileName": file_name,
            }
        )

    return ok(results, message=f"已接收 {len(results)} 个文件，正在后台处理")


# ------------------------------------------------------------------
# 手动录入
# ------------------------------------------------------------------
@router.post("/collections/{collection_id}/documents/manual", dependencies=[Depends(verify_jwt)])
async def create_manual_document(
    collection_id: str,
    req: ManualDocumentCreateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """手动录入一条知识（仅知识库所有者）。"""
    require_collection_owner(user_id, collection_id)
    _require_collection(db, collection_id)
    svc = DocumentService(db)
    doc = svc.create_manual_doc(collection_id, req.title, req.content)
    task_id = submit_ingest(background_tasks, doc.id)
    svc.mark_task(doc, task_id)
    return ok(
        {"documentId": doc.id, "taskId": task_id, "title": doc.title},
        message="已录入，正在后台向量化",
    )


# ------------------------------------------------------------------
# 列表 / 详情
# ------------------------------------------------------------------
@router.get("/collections/{collection_id}/documents", dependencies=[Depends(verify_jwt)])
async def list_documents(
    collection_id: str,
    status: str = Query(None),
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """文档列表（含处理状态与进度；仅知识库所有者）。"""
    require_collection_owner(user_id, collection_id)
    _require_collection(db, collection_id)
    docs = DocumentService(db).list_by_collection(collection_id, status)
    return ok({"items": [d.to_dict() for d in docs], "total": len(docs)})


@router.get("/documents/{doc_id}", dependencies=[Depends(verify_jwt)])
async def get_document(
    doc_id: str,
    withChunks: bool = Query(False),
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """文档详情，可选返回切片预览（仅知识库所有者）。"""
    require_document_owner(user_id, doc_id)
    doc = _require_document(db, doc_id)
    data = doc.to_dict(with_content=True)
    if withChunks:
        chunks = DocumentService(db).list_chunks(doc_id)
        data["chunks"] = [c.to_dict() for c in chunks]
    return ok(data)


# ------------------------------------------------------------------
# 编辑（仅手动录入的文档）
# ------------------------------------------------------------------
@router.put("/documents/{doc_id}", dependencies=[Depends(verify_jwt)])
async def update_document(
    doc_id: str,
    req: DocumentUpdateRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """编辑手动知识，触发重新向量化（仅知识库所有者）。"""
    require_document_owner(user_id, doc_id)
    doc = _require_document(db, doc_id)
    if doc.source_type != "manual":
        raise HTTPException(status_code=400, detail="仅手动录入的知识支持编辑")

    svc = DocumentService(db)
    # 先清旧向量与切片
    vector_ids = svc.reset_for_reindex(doc)
    if vector_ids:
        try:
            get_vector_store().delete_chunks(doc.collection_id, vector_ids)
        except Exception as e:
            print(f"[documents] 清理旧向量失败: {e}")

    doc = svc.update_manual_doc(doc, req.title, req.content)
    task_id = submit_ingest(background_tasks, doc.id)
    svc.mark_task(doc, task_id)
    return ok({"documentId": doc.id, "taskId": task_id}, message="已更新，正在重新向量化")


# ------------------------------------------------------------------
# 重建索引
# ------------------------------------------------------------------
@router.post("/documents/{doc_id}/reindex", dependencies=[Depends(verify_jwt)])
async def reindex_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """重新解析 + 向量化（仅知识库所有者）。"""
    require_document_owner(user_id, doc_id)
    doc = _require_document(db, doc_id)
    svc = DocumentService(db)

    vector_ids = svc.reset_for_reindex(doc)
    if vector_ids:
        try:
            get_vector_store().delete_chunks(doc.collection_id, vector_ids)
        except Exception as e:
            print(f"[documents] 清理旧向量失败: {e}")

    task_id = submit_ingest(background_tasks, doc.id)
    svc.mark_task(doc, task_id)
    return ok({"documentId": doc.id, "taskId": task_id}, message="已提交重建")


# ------------------------------------------------------------------
# 删除
# ------------------------------------------------------------------
@router.delete("/documents/{doc_id}", dependencies=[Depends(verify_jwt)])
async def delete_document(
    doc_id: str,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """删除文档（清理切片 + 向量；仅知识库所有者）。"""
    require_document_owner(user_id, doc_id)
    doc = _require_document(db, doc_id)
    svc = DocumentService(db)
    collection_id = doc.collection_id

    vector_ids = svc.prepare_delete(doc)
    if vector_ids:
        try:
            get_vector_store().delete_chunks(collection_id, vector_ids)
        except Exception as e:
            print(f"[documents] 删除向量失败（元数据已清理）: {e}")

    CollectionService(db).refresh_counts(collection_id)
    return ok({"id": doc_id}, message="删除成功")
