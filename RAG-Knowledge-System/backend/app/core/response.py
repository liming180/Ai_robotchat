"""
统一响应格式。
与主服务 backend/app/schemas/common.py 对齐：
    { success, message, data, error, timestamp }

注意：Java 后端的 Result 是 { code, message, data, timestamp }，
两套格式不同；知识库系统（FastAPI）统一使用本文件的格式，
前端拦截器请按 success 字段判断成败，不要按 code。
"""

from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """标准响应体。"""

    success: bool
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime


def ok(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
    """构造成功响应。"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
        "timestamp": datetime.now().isoformat(),
    }


def fail(
    message: str = "操作失败",
    code: str = "ERROR",
    details: Any = None,
    data: Any = None,
) -> Dict[str, Any]:
    """构造失败响应。"""
    return {
        "success": False,
        "message": message,
        "data": data,
        "error": {"code": code, "message": message, "details": details},
        "timestamp": datetime.now().isoformat(),
    }
