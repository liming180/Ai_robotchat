"""
数据库初始化脚本
自动创建所有 SQLAlchemy 模型对应的表
用法：python init_db.py
"""
from app.database import engine, Base
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.companion import Companion, UserCompanion
from app.models.memory import UserMemory, UserMood


def init_database():
    """创建所有表（逐表创建，兼容性差的表跳过而不中断）"""
    print("正在初始化数据库...")

    if engine is None:
        print("[ERROR] 数据库引擎未初始化，请检查 DATABASE_URL 配置。")
        print("[HINT] 如果使用 PostgreSQL，请确保安装了 psycopg2-binary: pip install psycopg2-binary")
        print("[HINT] 如果使用 MySQL，请确保安装了 pymysql: pip install pymysql")
        print("[HINT] 如果使用 SQLite，确保路径正确。")
        return

    # 逐表创建：遇到不兼容的类型（如 SQLite 下的 ARRAY）跳过该表，不影响其余表
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
        print("[WARNING] 以下表因类型不兼容被跳过（不影响记忆/心情核心功能）:")
        for name, err in skipped:
            print(f"  - {name}: {err}")
        print("[HINT] 项目模型使用了 PostgreSQL 特有类型（UUID/ARRAY）。")
        print("[HINT] 如需在 MySQL/SQLite 下创建这些表，需将模型中的 ARRAY 改为 JSON、UUID 改为 String(36)。")

    # 打印最终所有表
    inspector = inspect(engine)
    print(f"数据库现有表: {inspector.get_table_names()}")


if __name__ == "__main__":
    init_database()
