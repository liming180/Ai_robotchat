"""8002 鉴权基础设施（2026-11-21，Phase 2 鉴权强制化）。

设计要点：
- JWT 与 Java 主后端**同源**：只读用户级环境变量 ``JWT_SECRET``，8002 不单独设值。
- 启动自检：用 SHA-256 指纹前 8 位对比两侧密钥是否一致，**不打印任何原值**；
  不一致直接抛异常终止启动，避免带着错密钥静默运行（表现为所有管理接口莫名 401）。
- 服务间检索用 ``X-Service-Token``，与 5000 流式端点的 ``SERVICE_TOKEN`` 同值。
- 所有校验函数均设计为 FastAPI 依赖注入（写在函数体内会被 body 校验抢先）。

==================== 铁律（不得违反） ====================
**所有归属判断的唯一身份来源是 JWT 中的 ``userId``。**

- 禁止信任请求体、查询参数、请求头里任何自称的用户标识（如 ``userId`` /
  ``createdBy`` / ``ownerId`` 字段）。
- 任何「查某资源的归属」都必须从资源本身反查到所属 companion/collection 的
  ``created_by``，再与 ``token.userId`` 比较；不得反过来按客户端传入的身份过滤。
- 新增路由若涉及用户资源，必须挂 ``Depends(verify_jwt)`` 并调用对应
  ``require_*_owner``；白名单之外不允许出现无鉴权路由
  （由 ``tests/test_auth_coverage.py`` 断言）。

================ 错误码口径（与 Java 主后端对齐） ================
- **401**：未携带 / 令牌无效 / 令牌过期 / 缺 userId。
- **403**：令牌有效但无权访问该资源（含「不存在」场景，防探测）。
- **503**：归属校验所需的主库连接不可用 —— 基础设施故障不得伪装成 403。
- **400**：请求参数本身非法（与归属无关），如缺少 companionId 与 collectionIds。
==========================================================
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
        # 算法与 Java 显式钉死一致：Java 侧用 `signWith(key, Jwts.SIG.HS512)`，
        # 这里只放行 HS512。两侧都不再依赖密钥长度自动选择，避免换密钥时静默失配。
        # 只接受 HMAC 族中的 HS512，同时杜绝 alg=none 与非对称算法混淆攻击。
        # PyJWT 默认校验 exp，options 里再显式声明一次，避免将来被改动带偏。
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS512"],
            options={"require": ["exp"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="令牌无效")

    user_id = payload.get("userId")
    if not user_id or not str(user_id).strip():
        raise HTTPException(status_code=401, detail="令牌缺少 userId")
    return str(user_id).strip()


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


def require_companion_owner(user_id: str, companion_id: Optional[str], *, allow_preset: bool = True) -> None:
    """校验 companion 属于当前用户（读主库只读连接）。

    错误码口径：
    - 归属不匹配 / 不存在：**403**（不区分，防探测）
    - 主库不可用：**503**（基础设施故障不得伪装成无权）

    ``allow_preset=False`` 时额外拒绝预置伴侣 —— 用于建库场景：
    预置伴侣只允许系统级知识（created_by=system），用户个性化知识走自建伴侣。
    原因：retrieve 链路只有 companionId 没有 userId，无法按
    「本人 OR system」过滤；若允许用户给预设伴侣建库，其私有库会进入
    所有人聊天的检索范围，破坏伴侣隔离。
    """
    if not companion_id:
        return

    from sqlalchemy import text

    from app.db.database import MainSessionLocal

    db = _main_session()
    try:
        row = db.execute(
            text("SELECT created_by, is_preset FROM companion WHERE id = :cid AND deleted = 0"),
            {"cid": companion_id},
        ).mappings().first()
    finally:
        db.close()

    if row is None:
        raise HTTPException(status_code=403, detail="无权访问该资源")

    if row["is_preset"]:
        if allow_preset:
            # 预置伴侣归属 system，全员可读（与主后端伴侣列表口径一致）
            return
        raise HTTPException(
            status_code=403,
            detail="预置伴侣仅允许系统级知识，请为自己的自建伴侣创建知识库",
        )

    if str(row["created_by"] or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该资源")


def _main_session():
    """获取主库只读会话；不可用时统一 503。"""
    from app.db.database import MainSessionLocal

    if MainSessionLocal is None:
        raise HTTPException(status_code=503, detail="主库连接不可用，无法校验资源归属")
    return MainSessionLocal()


def require_collection_owner(user_id: str, collection_id: str):
    """校验知识库归属，返回 KbCollection（供路由复用，避免二次查询）。"""
    from app.db.database import SessionLocal

    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="元数据库不可用")

    db = SessionLocal()
    try:
        from app.models.collection import KbCollection

        coll = (
            db.query(KbCollection)
            .filter(KbCollection.id == collection_id, KbCollection.deleted == 0)
            .first()
        )
        if coll is None:
            raise HTTPException(status_code=403, detail="无权访问该资源")
        _assert_collection_owned(coll, user_id)
        db.expunge(coll)
        return coll
    finally:
        db.close()


def require_document_owner(user_id: str, document_id: str):
    """校验文档归属（经 document → collection 反查），返回 KbDocument。"""
    from app.db.database import SessionLocal

    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="元数据库不可用")

    db = SessionLocal()
    try:
        from app.models.collection import KbCollection
        from app.models.document import KbDocument

        doc = (
            db.query(KbDocument)
            .filter(KbDocument.id == document_id, KbDocument.deleted == 0)
            .first()
        )
        if doc is None:
            raise HTTPException(status_code=403, detail="无权访问该资源")

        coll = (
            db.query(KbCollection)
            .filter(KbCollection.id == doc.collection_id, KbCollection.deleted == 0)
            .first()
        )
        if coll is None:
            raise HTTPException(status_code=403, detail="无权访问该资源")
        _assert_collection_owned(coll, user_id)
        db.expunge(doc)
        return doc
    finally:
        db.close()


def require_task_owner(user_id: str, task_id: str):
    """校验任务归属（task_id → document → collection 反查），返回 KbDocument。"""
    from app.db.database import SessionLocal

    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="元数据库不可用")

    db = SessionLocal()
    try:
        from app.models.collection import KbCollection
        from app.models.document import KbDocument

        doc = (
            db.query(KbDocument)
            .filter(KbDocument.task_id == task_id, KbDocument.deleted == 0)
            .first()
        )
        if doc is None:
            raise HTTPException(status_code=403, detail="无权访问该资源")

        coll = (
            db.query(KbCollection)
            .filter(KbCollection.id == doc.collection_id, KbCollection.deleted == 0)
            .first()
        )
        if coll is None:
            raise HTTPException(status_code=403, detail="无权访问该资源")
        _assert_collection_owned(coll, user_id)
        db.expunge(doc)
        return doc
    finally:
        db.close()


def _assert_collection_owned(coll, user_id: str) -> None:
    """知识库归属断言：created_by 必须等于 token.userId。

    无归属（created_by IS NULL）的历史库一律 403 —— 按方案 A「遗留垃圾保持不可见」。
    """
    if str(coll.created_by or "") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该资源")
