"""
角色列表接口（鉴权强制化：需 JWT，且按 token.userId 过滤）。
只读主库 ai_companion.companion，供前端「绑定角色」下拉框使用。
注意：表名是 companion（单数），预设角色 ID 形如 preset-1，自定义为 UUID。

过滤口径：返回「系统预置伴侣 + 本人自建伴侣」。
身份**只取 token.userId**，不接受任何客户端传入的用户标识（见 security.py 铁律）。
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.response import ok
from app.core.security import verify_jwt
from app.db.database import MainSessionLocal

router = APIRouter()

_SQL = """
SELECT id, name, avatar, description, category, personality
FROM companion
WHERE deleted = 0
  AND (is_preset = 1 OR created_by = :user_id)
ORDER BY is_preset DESC, created_at ASC
"""


@router.get("/companions", dependencies=[Depends(verify_jwt)])
async def list_companions(user_id: str = Depends(verify_jwt)):
    """读取主库角色列表（预置 + 本人自建）。"""
    if MainSessionLocal is None:
        raise HTTPException(status_code=503, detail="主库连接不可用，无法读取角色列表")

    db = MainSessionLocal()
    try:
        rows = db.execute(__import__("sqlalchemy").text(_SQL), {"user_id": user_id}).mappings().all()
        return ok(
            {
                "items": [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "avatar": r["avatar"],
                        "description": r["description"],
                        "category": r["category"],
                        "personality": r["personality"],
                    }
                    for r in rows
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取角色列表失败: {str(e)[:200]}")
    finally:
        db.close()
