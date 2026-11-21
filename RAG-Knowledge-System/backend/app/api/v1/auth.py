"""
登录转发接口（2026-11-17 前端方案新增）。

RAG 管理前端（RAG-Knowledge-System/frontend，端口 3001）没有独立账号体系：
登录时由本接口把邮箱/密码原样转发给 Java 业务后端（8081 /api/v1/auth/login），
验证通过后返回 Java 签发的 JWT（accessToken 有效期 2 小时）。
RAG 侧不建账号表；Phase 2 鉴权强制化时共享 JWT_SECRET 验签。

响应归一化：Java 的 Result 是 {code, message, data, timestamp}，
本接口转成 RAG 统一响应 {success, message, data, ...}（见 app/core/response.py）。
"""

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.response import ok

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/login")
async def login(payload: LoginRequest):
    """转发 Java 8081 登录，成功返回 {accessToken, refreshToken, tokenType, user}。"""
    url = f"{settings.java_auth_url.rstrip('/')}/api/v1/auth/login"
    try:
        # 本机服务间请求不走终端继承的 HTTP 代理；代理可能把 localhost 请求
        # 直接转成 502，且不会留下 Java 请求日志。
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            resp = await client.post(url, json={"email": payload.email, "password": payload.password})
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"登录服务不可达: {url}（{type(e).__name__}）")

    body: dict = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}

    if resp.status_code == 200 and body.get("code") == 200:
        return ok(body.get("data"), message=body.get("message") or "登录成功")

    # 只有 Java 明确的鉴权拒绝才映射 401；上游 5xx 保留 502，
    # 避免把服务故障误报为密码错误。
    if resp.status_code >= 500:
        message = body.get("message") or f"Java 登录服务异常（HTTP {resp.status_code}）"
        raise HTTPException(status_code=502, detail=message)
    message = body.get("message") or f"登录失败（Java HTTP {resp.status_code}）"
    raise HTTPException(status_code=401, detail=message)
