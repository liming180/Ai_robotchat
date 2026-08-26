"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLAlchemy engine
# 如果 database_url 无效，engine 设为 None，避免服务启动崩溃
try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.app_debug
    )
    # 测试连接
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"[WARNING] 数据库连接失败: {e}")
    print(f"[WARNING] 当前 DATABASE_URL: {settings.database_url}")
    print("[WARNING] 记忆系统需要数据库支持，请检查配置。AI 聊天功能仍可用。")
    engine = None

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database sessions.
    Used in FastAPI endpoints to provide a database session.
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未配置或连接失败")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
