"""
RAG 知识库系统 - FastAPI 入口
默认端口 8002

启动：
    cd RAG-Knowledge-System/backend
    python main.py
文档：
    http://localhost:8002/docs
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.response import fail, ok  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[RAG-KB] 启动中 ... env={settings.app_env} port={settings.app_port}")
    print(f"[RAG-KB] 元数据库: {settings.database_url.split('@')[-1]}")
    print(f"[RAG-KB] 向量库后端: {settings.vector_store_backend}")
    print(f"[RAG-KB] 允许的上传格式: {settings.allowed_extensions_list}")

    # 鉴权自检：密钥与 Java 不同源时直接失败，不带着错密钥静默运行。
    from app.core.security import verify_secret_alignment

    fingerprint = verify_secret_alignment()
    print(f"[RAG-KB] JWT_SECRET 指纹: {fingerprint}（仅指纹，不打印原值）")
    if settings.service_token:
        print("[RAG-KB] SERVICE_TOKEN 已配置，/retrieve 将校验 X-Service-Token")
    else:
        print("[RAG-KB] [WARN] SERVICE_TOKEN 未配置，/retrieve 不校验（仅适合本地开发）")
    yield
    print("[RAG-KB] 已关闭")


app = FastAPI(
    title="RAG Knowledge System",
    description="独立部署的 RAG 知识库系统，为 AI 伴侣提供角色专属知识检索",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # 从通配 * 收紧到显式来源（默认 RAG 管理前端 3001）。
    # allow_credentials=True 时浏览器禁止 *，这也是必须显式列出的原因之一。
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# 全局异常处理：统一成 {success, message, data, error, timestamp}
# ------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(str(exc.detail), code=f"HTTP_{exc.status_code}"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=fail("参数校验失败", code="VALIDATION_ERROR", details=exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(f"[RAG-KB] 未处理异常: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content=fail(f"服务器内部错误: {str(exc)[:200]}", code="INTERNAL_ERROR"),
    )


# ------------------------------------------------------------------
# 路由注册
# ------------------------------------------------------------------
from app.api.v1 import auth, collections, companions, documents, retrieve, tasks  # noqa: E402

app.include_router(collections.router, prefix="/api/v1/kb", tags=["Collections"])
app.include_router(documents.router, prefix="/api/v1/kb", tags=["Documents"])
app.include_router(retrieve.router, prefix="/api/v1/kb", tags=["Retrieve"])
app.include_router(tasks.router, prefix="/api/v1/kb", tags=["Tasks"])
app.include_router(companions.router, prefix="/api/v1/kb", tags=["Companions"])
app.include_router(auth.router)  # 登录转发：/api/v1/auth/login（自有前缀，不挂在 /kb 下）


# ------------------------------------------------------------------
# 系统接口
# ------------------------------------------------------------------
@app.get("/health", tags=["System"])
async def health():
    """健康检查。"""
    from app.db.database import engine, main_engine

    return ok(
        {
            "service": settings.app_name,
            "version": "0.1.0",
            "env": settings.app_env,
            "database": "connected" if engine is not None else "unavailable",
            "mainDatabase": "connected" if main_engine is not None else "unavailable",
            "embeddingConfigured": True,  # 本地哈希向量，恒可用
        },
        message="healthy",
    )


@app.get("/", tags=["System"])
async def root():
    """根路径，给出常用入口。"""
    return ok(
        {
            "docs": "/docs",
            "health": "/health",
            "apiPrefix": "/api/v1/kb",
        },
        message="RAG Knowledge System",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
