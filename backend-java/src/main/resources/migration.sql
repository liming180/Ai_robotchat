-- ============================================================
-- 增量迁移脚本（针对已存在的库）
-- schema.sql 用的是 CREATE TABLE IF NOT EXISTS，老库不会自动加列，
-- 升级既有环境时手动执行本文件。
-- 用法：mysql -uroot -p ai_companion < migration.sql
-- ============================================================

USE ai_companion;

-- 2026-11-12 P0-7：message 表新增 images 列（存图片 URL 的 JSON 数组字符串）
-- MySQL 8.0 不支持 ADD COLUMN IF NOT EXISTS，若已存在会报 1060，可忽略。
ALTER TABLE message ADD COLUMN images TEXT NULL AFTER content;
