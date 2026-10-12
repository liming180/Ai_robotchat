"""
数据库连接与会话管理。
风格对齐主服务 backend/app/database.py：连接失败只告警，不阻断服务启动。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()

engine = None
SessionLocal = None

try:
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(settings.database_url, echo=settings.db_echo)
    else:
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.db_echo,
        )

    # 测试连接，失败则降级为 None
    with engine.connect():
        pass

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"[WARNING] 数据库连接失败: {e}")
    print(f"[WARNING] 当前 DATABASE_URL: {settings.database_url}")
    print("[WARNING] 知识库元数据功能不可用，请检查 MySQL 是否启动、rag_knowledge 库是否已创建。")
    engine = None
    SessionLocal = None


# ---- 主库只读引擎（角色列表用）----
main_engine = None
MainSessionLocal = None
try:
    main_engine = create_engine(
        settings.main_database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    with main_engine.connect():
        pass
    MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)
except Exception as e:
    print(f"[WARNING] 主库连接失败（角色列表不可用）: {e}")
    main_engine = None
    MainSessionLocal = None


def get_db():
    """FastAPI 依赖：提供知识库元数据会话。"""
    if SessionLocal is None:
        raise RuntimeError("数据库未配置或连接失败")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
