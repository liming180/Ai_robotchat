"""
角色列表接口。
只读主库 ai_companion.companion，供前端"绑定角色"下拉框使用。
注意：表名是 companion（单数），预设角色 ID 形如 preset-1，自定义为 UUID。
"""

from fastapi import APIRouter, HTTPException

from app.core.response import ok
from app.db.database import MainSessionLocal

router = APIRouter()

_SQL = """
SELECT id, name, avatar, description, category, personality
FROM companion
WHERE deleted = 0
ORDER BY is_preset DESC, created_at ASC
"""


@router.get("/companions")
async def list_companions():
    """读取主库角色列表（只读）。"""
    if MainSessionLocal is None:
        raise HTTPException(status_code=503, detail="主库连接不可用，无法读取角色列表")

    db = MainSessionLocal()
    try:
        rows = db.execute(__import__("sqlalchemy").text(_SQL)).mappings().all()
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
