-- ============================================================
-- RAG 知识库系统 建表脚本（MySQL 8.x）
-- 共用主项目 MySQL 实例，独立 database：rag_knowledge
-- 执行：mysql -u root -p < sql/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS rag_knowledge
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE rag_knowledge;

-- ------------------------------------------------------------
-- 知识库集合：一个集合绑定一个 companion（也可不绑定，作为公共库）
-- companion_id 跨服务引用主库 ai_companion.companion.id，不设外键
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kb_collection (
    id                VARCHAR(36)  PRIMARY KEY COMMENT '主键 UUID',
    name              VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description       TEXT         NULL COMMENT '描述',
    companion_id      VARCHAR(36)  NULL COMMENT '绑定的 AI 伴侣 ID（跨服务引用）',
    parser_config     JSON         NULL COMMENT 'JSON 解析规则 {"itemsPath","contentField","titleField"}',
    embedding_model   VARCHAR(50)  NOT NULL DEFAULT 'embedding-3' COMMENT '写入后不可变',
    embedding_dim     INT          NOT NULL DEFAULT 2048 COMMENT '写入后不可变，防止维度污染',
    embedding_backend VARCHAR(20)  NOT NULL DEFAULT 'zhipu' COMMENT '写入后不可变',
    chunk_size        INT          NOT NULL DEFAULT 500,
    chunk_overlap     INT          NOT NULL DEFAULT 50,
    document_count    INT          NOT NULL DEFAULT 0,
    chunk_count       INT          NOT NULL DEFAULT 0,
    status            VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT 'active / disabled',
    created_by        VARCHAR(36)  NULL,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted           TINYINT(1)   NOT NULL DEFAULT 0,
    KEY idx_kb_collection_companion (companion_id),
    KEY idx_kb_collection_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库集合';

-- ------------------------------------------------------------
-- 文档：一个上传文件，或一条手动录入的知识
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kb_document (
    id            VARCHAR(36)  PRIMARY KEY,
    collection_id VARCHAR(36)  NOT NULL,
    source_type   VARCHAR(20)  NOT NULL COMMENT 'file / manual',
    title         VARCHAR(255) NOT NULL,
    file_name     VARCHAR(255) NULL,
    file_ext      VARCHAR(20)  NULL COMMENT 'json / md / txt',
    file_size     BIGINT       NULL,
    file_path     VARCHAR(500) NULL,
    raw_content   LONGTEXT     NULL COMMENT '手动录入内容或解析后文本',
    status        VARCHAR(20)  NOT NULL DEFAULT 'pending'
                  COMMENT 'pending/parsing/chunking/embedding/completed/failed',
    progress      INT          NOT NULL DEFAULT 0 COMMENT '0-100',
    error_msg     TEXT         NULL,
    task_id       VARCHAR(64)  NULL COMMENT '异步任务 ID，前端轮询用',
    chunk_count   INT          NOT NULL DEFAULT 0,
    created_by    VARCHAR(36)  NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted       TINYINT(1)   NOT NULL DEFAULT 0,
    KEY idx_kb_doc_collection (collection_id, status),
    KEY idx_kb_doc_task (task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识文档';

-- ------------------------------------------------------------
-- 切片：便于精确删除、结果回溯、调试
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kb_chunk (
    id            VARCHAR(36)  PRIMARY KEY,
    document_id   VARCHAR(36)  NOT NULL,
    collection_id VARCHAR(36)  NOT NULL,
    chunk_index   INT          NOT NULL,
    content       TEXT         NOT NULL,
    char_count    INT          NOT NULL DEFAULT 0,
    vector_id     VARCHAR(128) NOT NULL COMMENT 'Chroma 中的 id',
    meta          JSON         NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_kb_chunk_doc (document_id),
    KEY idx_kb_chunk_collection (collection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识切片';
