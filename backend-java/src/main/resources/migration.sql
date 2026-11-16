-- ============================================================
-- 增量迁移脚本（针对已存在的库）
-- schema.sql 用的是 CREATE TABLE IF NOT EXISTS，老库不会自动加列，
-- 升级既有环境时手动执行本文件。
-- 用法：mysql -uroot -p ai_companion < migration.sql
-- ============================================================

USE ai_companion;

-- 2026-11-12 P0-7：message 表新增 images 列（存图片 URL 的 JSON 数组字符串）
-- MySQL 8.0 不支持 ADD COLUMN IF NOT EXISTS，若已存在会报 1060，可忽略。
-- ⚠ 本行在已升级过的库上会报 1060，mysql CLI 默认遇错即中断，**后续语句不会执行**。
--   执行方式二选一：
--     a) mysql ... --force < migration.sql   （遇错继续，推荐）
--     b) 只执行本次需要的语句，跳过已应用的旧语句
ALTER TABLE message ADD COLUMN images TEXT NULL AFTER content;

-- 2026-11-16 任务十一：笔记功能建表（新建 note 表，含级联删除所需的复合索引）
CREATE TABLE IF NOT EXISTS note (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    companion_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    tags VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT(1) NOT NULL DEFAULT 0,
    KEY idx_note_user_updated (user_id, updated_at),
    KEY idx_note_companion_deleted (companion_id, deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
