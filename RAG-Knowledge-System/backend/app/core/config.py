"""
知识库系统配置管理。
风格对齐主服务 backend/app/config.py（Pydantic Settings + .env）。
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，全部可通过环境变量或 .env 覆盖。"""

    # ---- 应用 ----
    app_name: str = "RAG_Knowledge_System"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8002
    app_debug: bool = True

    # ---- 元数据库：共用 MySQL 实例，独立 database ----
    database_url: str = (
        "mysql+pymysql://root:asdfghjkl54321@localhost:3306/rag_knowledge?charset=utf8mb4"
    )
    # SQL 日志开关（与 app_debug 解耦，避免日志爆炸）
    db_echo: bool = False

    # ---- 主库只读连接（角色列表用）----
    main_database_url: str = (
        "mysql+pymysql://root:asdfghjkl54321@localhost:3306/ai_companion?charset=utf8mb4"
    )

    # ---- 向量库 ----
    chroma_persist_dir: str = "./storage/chroma_db"

    # ---- Embedding（本地哈希向量，无外部依赖）----
    embedding_model: str = "simple-hash"
    embedding_dim: int = 256

    # ---- 上传 ----
    upload_dir: str = "./storage/uploads"
    max_file_size_mb: int = 20
    allowed_extensions: str = "json,md,txt"

    # ---- 切片默认值 ----
    default_chunk_size: int = 500
    default_chunk_overlap: int = 50

    # ---- 检索 ----
    retrieve_top_k: int = 4
    retrieve_score_threshold: float = 0.0

    # ---- 主服务 JWT（二期启用）----
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    # ---- Redis（二期异步队列，db 2）----
    redis_url: str = "redis://localhost:6379/2"

    @property
    def allowed_extensions_list(self) -> List[str]:
        """把 "json,md,txt" 解析成 ["json", "md", "txt"]。"""
        return [
            e.strip().lower().lstrip(".")
            for e in self.allowed_extensions.split(",")
            if e.strip()
        ]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
