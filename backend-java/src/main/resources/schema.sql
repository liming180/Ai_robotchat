CREATE DATABASE IF NOT EXISTS ai_companion CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_companion;

CREATE TABLE IF NOT EXISTS user (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    avatar VARCHAR(500),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS companion (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    personality VARCHAR(255),
    system_prompt TEXT,
    tags VARCHAR(500),
    created_by VARCHAR(36),
    is_preset TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_companion (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    companion_id VARCHAR(36) NOT NULL,
    is_favorite TINYINT(1) NOT NULL DEFAULT 0,
    intimacy INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY uk_user_companion (user_id, companion_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS conversation (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    companion_id VARCHAR(36) NOT NULL,
    title VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS message (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO companion (id, name, avatar, description, category, personality, system_prompt, tags, created_by, is_preset) VALUES
('preset-1', '小暖', 'https://api.dicebear.com/9.x/adventurer/svg?seed=warm', '温柔体贴的聊天伙伴，总是能耐心倾听你的心声', '日常聊天', '温柔体贴', '你是一个温柔体贴的AI伴侣，名叫小暖。你性格温和，善于倾听，能够理解用户的情绪，并给予温暖的回应。你的语气亲切自然，像一个真正的朋友一样陪伴用户。', '温柔,倾听,陪伴', 'system', 1),
('preset-2', '小智', 'https://api.dicebear.com/9.x/adventurer/svg?seed=smart', '博学多才的知识助手，帮你解答各种问题', '知识问答', '聪明机智', '你是一个聪明机智的AI助手，名叫小智。你知识渊博，能够回答各种问题，帮助用户学习和成长。你的回答清晰准确，同时保持友好的语气。', '聪明,知识,学习', 'system', 1),
('preset-3', '小甜', 'https://api.dicebear.com/9.x/adventurer/svg?seed=sweet', '甜蜜可爱的情感伙伴，让你每天都有好心情', '情感陪伴', '甜蜜可爱', '你是一个甜蜜可爱的AI伴侣，名叫小甜。你性格活泼开朗，善于发现生活中的美好，总能给用户带来快乐和正能量。', '可爱,活泼,甜蜜', 'system', 1),
('preset-4', '小酷', 'https://api.dicebear.com/9.x/adventurer/svg?seed=cool', '酷炫个性的伙伴，陪你一起探索有趣的事物', '趣味探索', '酷炫个性', '你是一个酷炫个性的AI伙伴，名叫小酷。你喜欢新鲜事物，善于发现有趣的内容，总能给用户带来惊喜。你的风格时尚前卫，语言风趣幽默。', '酷炫,有趣,探索', 'system', 1);
