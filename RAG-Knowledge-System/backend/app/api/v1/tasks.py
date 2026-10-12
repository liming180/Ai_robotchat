"""
任务进度查询。
一期按 task_id 查 kb_document；二期接入 Celery 后可叠加 AsyncResult 状态。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import ok
from app.db.database import get_db
from app.models.document import KbDocument

router = APIRouter()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """按任务 ID 查询进度（前端轮询用）。"""
    doc = (
        db.query(KbDocument)
        .filter(KbDocument.task_id == task_id, KbDocument.deleted == 0)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return ok(
        {
            "taskId": task_id,
            "documentId": doc.id,
            "status": doc.status,
            "progress": doc.progress,
            "errorMsg": doc.error_msg,
            "chunkCount": doc.chunk_count,
        }
    )
