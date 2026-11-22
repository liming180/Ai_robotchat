"""
知识库系统配置管理。
风格对齐主服务 backend/app/config.py（Pydantic Settings + .env）。
"""

from typing import List

from pydantic import AliasChoices, Field
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
    # 密码不写默认值（本机在 .env 的 DATABASE_URL / MAIN_DATABASE_URL 注入）
    database_url: str = (
        "mysql+pymysql://root@localhost:3306/rag_knowledge?charset=utf8mb4"
    )
    # SQL 日志开关（与 app_debug 解耦，避免日志爆炸）
    db_echo: bool = False

    # ---- 主库只读连接（角色列表用）----
    main_database_url: str = (
        "mysql+pymysql://root@localhost:3306/ai_companion?charset=utf8mb4"
    )

    # ---- 向量库 ----
    # 存储后端选择：milvus（新）/ chroma（旧，保留回退）
    vector_store_backend: str = "milvus"

    # Chroma 配置（旧后端，保留回退）
    chroma_persist_dir: str = "./storage/chroma_db"

    # Milvus 配置（新后端，2026-11-19）
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_user: str = ""  # 留空表示无认证
    milvus_password: str = ""

    # ---- Rerank（TEI 自托管，2026-11-19）----
    # 开关关闭时检索走纯 COSINE，行为与接入前逐字节一致
    rerank_enabled: bool = False
    # 注意：这是 Milvus 容器视角的地址（docker compose 服务名），不能写 localhost
    tei_endpoint: str = "http://tei:80"

    # ---- Embedding ----
    # Chroma 旧后端：本地哈希向量（256 维）
    # 默认值对应当前 Milvus 后端；Chroma 回退时由 CollectionService 固定写旧配置。
    embedding_model: str = "embedding-3"
    embedding_dim: int = 2048

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

    # ---- 主服务 JWT（Phase 2 鉴权强制化，2026-11-21）----
    # 必须与 Java 同源：只读用户级环境变量 JWT_SECRET，8002 不单独设值。
    # 显式指定 validation_alias，避免按字段名自动匹配出 JWT_SECRET_KEY 等
    # 历史变体（曾因此读到一个 64 位旧密钥，两侧不同源却无报错）。
    # 默认空串 → 启动自检直接失败，不会带错密钥静默运行。
    jwt_secret_key: str = Field(default="", validation_alias=AliasChoices("JWT_SECRET", "jwt_secret_key"))

    # ---- 服务间共享密钥（5000 → 8002 检索）----
    # 留空则不校验（仅本地开发）；与 backend/.env 的 SERVICE_TOKEN 同值。
    service_token: str = ""

    # ---- CORS ----
    # 逗号分隔的允许来源，默认只放行 RAG 管理前端 3001。
    cors_origins: str = "http://localhost:3001,http://127.0.0.1:3001"

    # ---- Java 业务后端（登录转发用，2026-11-17 前端方案）----
    java_auth_url: str = "http://localhost:8081"

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
