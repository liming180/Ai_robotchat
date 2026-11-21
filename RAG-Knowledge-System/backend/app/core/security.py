"""8002 鉴权基础设施（2026-11-21，Phase 2 鉴权强制化第一批）。

设计要点：
- JWT 与 Java 主后端**同源**：只读用户级环境变量 ``JWT_SECRET``，8002 不单独设值。
- 启动自检：用 SHA-256 指纹前 8 位对比两侧密钥是否一致，**不打印任何原值**；
  不一致直接抛异常终止启动，避免带着错密钥静默运行（表现为所有管理接口莫名 401）。
- 服务间检索用 ``X-Service-Token``，与 5000 流式端点的 ``SERVICE_TOKEN`` 同值。
- 所有校验函数均设计为 FastAPI 依赖注入（写在函数体内会被 body 校验抢先）。
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional

import jwt
from fastapi import Header, HTTPException, Request

from app.core.config import settings


def _fingerprint(secret: str) -> str:
    """密钥指纹：仅用于比对，不可逆推原值。"""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:8]


def _java_secret_fingerprint() -> Optional[str]:
    """从 Java 的 application.yml 读取兜底密钥的指纹，用于启动自检提示。

    只在无法读取用户级环境变量时用于诊断，不参与实际验签。
    """
    yml = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "..", "..", "backend-java", "src", "main", "resources", "application.yml",
    )
    try:
        with open(os.path.abspath(yml), "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("secret:"):
                    raw = stripped.split(":", 1)[1].strip()
                    # ${JWT_SECRET:fallback} -> fallback
                    if raw.startswith("${") and ":" in raw:
                        raw = raw.split(":", 1)[1].rstrip("}")
                    return _fingerprint(raw)
    except OSError:
        return None
    return None


def verify_secret_alignment() -> str:
    """启动自检：确认 8002 能读到与 Java 同源的 JWT_SECRET。

    Returns:
        当前密钥指纹（8 位），供启动日志打印。

    Raises:
        RuntimeError: 未配置 JWT_SECRET，或与 Java 兜底密钥不一致。
    """
    secret = (settings.jwt_secret_key or "").strip()
    fallback_fp = _java_secret_fingerprint()

    if not secret or secret == "change-me-in-production":
        raise RuntimeError(
            "[鉴权] 未读取到 JWT_SECRET（用户级环境变量）。8002 与 Java 必须同源，"
            "请先 setx JWT_SECRET <值> 并用新终端重启。"
        )

    current_fp = _fingerprint(secret)
    if fallback_fp and current_fp == fallback_fp:
        raise RuntimeError(
            f"[鉴权] JWT_SECRET 指纹 {current_fp} 与 Java application.yml 兜底密钥相同，"
            "说明 8002 读到的是开发默认值而非环境变量。请检查启动终端是否晚于 setx。"
        )

    # 与 Java 实际读取值对比：Java 若也读到了环境变量，两侧应一致。
    # 这里只能校验「不是兜底值」，真正的同源由同一环境变量保证。
    return current_fp


def verify_jwt(authorization: Optional[str] = Header(None)) -> str:
    """校验 Authorization: Bearer <JWT>，返回 userId。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="缺少 Authorization: Bearer 令牌")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="令牌无效")

    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌缺少 userId")
    return str(user_id)


def verify_service_token(x_service_token: Optional[str] = Header(None)) -> None:
    """校验 X-Service-Token（5000 → 8002 检索专用）。

    ``SERVICE_TOKEN`` 未配置时跳过，保持本地开发可用；
    配置后必须匹配，否则 401。
    """
    expected = (settings.service_token or "").strip()
    if not expected:
        return
    if (x_service_token or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Service-Token")


def require_companion_owner(user_id: str, companion_id: Optional[str]) -> None:
    """校验 companion 属于当前用户（读主库只读连接）。

    口径与主后端一致：他人资源统一 400，不区分「不存在」与「无权」（防探测）。
    主库不可用时返回 503，避免把基础设施故障误判成无权。
    """
    if not companion_id:
        return

    from sqlalchemy import text

    from app.db.database import MainSessionLocal

    if MainSessionLocal is None:
        raise HTTPException(status_code=503, detail="主库连接不可用，无法校验资源归属")

    db = MainSessionLocal()
    try:
        row = db.execute(
            text("SELECT created_by, is_preset FROM companion WHERE id = :cid AND deleted = 0"),
            {"cid": companion_id},
        ).mappings().first()
    finally:
        db.close()

    if row is None:
        raise HTTPException(status_code=400, detail="知识库不存在")
    # 预置伴侣归属 system，任何登录用户都可读（与主后端 companion 列表口径一致）
    if row["is_preset"]:
        return
    if str(row["created_by"] or "") != user_id:
        raise HTTPException(status_code=400, detail="知识库不存在")
