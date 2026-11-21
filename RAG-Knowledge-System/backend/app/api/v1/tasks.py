"""
任务进度查询（鉴权强制化：需 JWT + 归属校验）。
一期按 task_id 查 kb_document；二期接入 Celery 后可叠加 AsyncResult 状态。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.response import ok
from app.core.security import require_task_owner, verify_jwt
from app.db.database import get_db
from app.models.document import KbDocument

router = APIRouter()


@router.get("/tasks/{task_id}", dependencies=[Depends(verify_jwt)])
async def get_task_status(
    task_id: str,
    user_id: str = Depends(verify_jwt),
    db: Session = Depends(get_db),
):
    """按任务 ID 查询进度（前端轮询用；仅知识库所有者）。"""
    # 归属经 task_id → document → collection 反查，不存在与无权统一 403
    require_task_owner(user_id, task_id)

    doc = (
        db.query(KbDocument)
        .filter(KbDocument.task_id == task_id, KbDocument.deleted == 0)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=403, detail="无权访问该资源")

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
