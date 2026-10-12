"""
数据库初始化脚本。
逐表创建，遇到不兼容的表跳过而不中断（风格对齐主服务 backend/init_db.py）。

用法：
    cd RAG-Knowledge-System/backend
    python -m app.db.init_db
"""

from sqlalchemy import inspect

from app.db.database import Base, engine

# 必须导入模型，否则 Base.metadata 里没有表定义
from app.models.chunk import KbChunk  # noqa: F401
from app.models.collection import KbCollection  # noqa: F401
from app.models.document import KbDocument  # noqa: F401


def init_database():
    """创建所有表。"""
    print("正在初始化 RAG 知识库数据库 ...")

    if engine is None:
        print("[ERROR] 数据库引擎未初始化，请检查 DATABASE_URL 配置。")
        print("[HINT] 先确认 MySQL 已启动，且已执行 sql/schema.sql 创建 rag_knowledge 库。")
        return

    created, skipped = [], []
    for table_name, table_obj in Base.metadata.tables.items():
        try:
            table_obj.create(bind=engine, checkfirst=True)
            created.append(table_name)
        except Exception as e:
            skipped.append((table_name, str(e).splitlines()[0]))

    print(f"[OK] 已就绪的表: {created}")
    if skipped:
        print("[WARNING] 以下表创建失败：")
        for name, err in skipped:
            print(f"  - {name}: {err}")

    inspector = inspect(engine)
    print(f"[INFO] 数据库现有表: {inspector.get_table_names()}")


if __name__ == "__main__":
    init_database()
