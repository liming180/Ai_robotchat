"""
数据库初始化脚本
创建 Python AI 服务负责的业务表（仅记忆 / 情绪）。

说明：用户 / 伴侣 / 对话 / 消息由 Java 业务后端写入 MySQL，不在本服务建表。
用法：python init_db.py
"""
from app.database import engine, Base
# 只需 import 模型，SQLAlchemy 才会把它注册进 Base.metadata
from app.models.memory import UserMemory, UserMood  # noqa: F401


def init_database():
    """创建所有表（逐表创建，单表失败不中断其余表）"""
    print("正在初始化数据库...")

    if engine is None:
        print("[ERROR] 数据库引擎未初始化，请检查 DATABASE_URL 配置。")
        print("[HINT] 如果使用 PostgreSQL，请确保安装了 psycopg2-binary: pip install psycopg2-binary")
        print("[HINT] 如果使用 MySQL，请确保安装了 pymysql: pip install pymysql")
        print("[HINT] 如果使用 SQLite，确保路径正确。")
        return

    from sqlalchemy import inspect
    skipped = []
    created = []
    for table_name, table_obj in Base.metadata.tables.items():
        try:
            table_obj.create(bind=engine, checkfirst=True)
            created.append(table_name)
        except Exception as e:
            skipped.append((table_name, str(e).splitlines()[0]))

    print(f"成功创建的表: {created}")
    if skipped:
        print("[WARNING] 以下表创建失败（不影响其余表）:")
        for name, err in skipped:
            print(f"  - {name}: {err}")

    inspector = inspect(engine)
    print(f"数据库现有表: {inspector.get_table_names()}")


if __name__ == "__main__":
    init_database()
