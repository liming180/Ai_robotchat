# AI 服务集成说明

## 概述

已成功集成智谱 AI（Zhipu AI）的大语言模型，使用 `glm-4-flash` 模型作为默认模型。

## API 密钥配置

- **API Key**: `4545b9e1adec45c08b53481a5a89759f.gXcXow7j1SmbmbcZ`
- **默认模型**: `glm-4-flash`
- **配置文件位置**: [backend/.env](file:///d:/Ai_robotchat/backend/.env)

## 项目结构更新

### 1. Python AI 服务

**更新文件**:
- [backend/requirements.txt](file:///d:/Ai_robotchat/backend/requirements.txt) - 添加了 `zhipuai` 依赖
- [backend/.env](file:///d:/Ai_robotchat/backend/.env) - 新增配置文件
- [backend/main.py](file:///d:/Ai_robotchat/backend/main.py) - 集成智谱 AI SDK

**主要功能**:
- 集成智谱 AI 官方 SDK
- 支持对话历史
- 支持系统提示词
- 异常处理和降级策略
- API 使用统计

### 2. Java 后端

**更新文件**:
- [backend-java/src/main/java/com/ai/companion/service/impl/ChatServiceImpl.java](file:///d:/Ai_robotchat/backend-java/src/main/java/com/ai/companion/service/impl/ChatServiceImpl.java) - 更新 AI 调用逻辑
- [backend-java/src/main/java/com/ai/companion/config/RestTemplateConfig.java](file:///d:/Ai_robotchat/backend-java/src/main/java/com/ai/companion/config/RestTemplateConfig.java) - 新增配置类

**主要功能**:
- 调用 Python AI 服务
- 传递对话历史
- 支持系统提示词（伴侣人设）
- 异常处理和降级

## 启动步骤

### 1. 启动 AI 服务

```bash
cd backend
pip install -r requirements.txt
python main.py
```

访问健康检查接口验证：http://localhost:5000/health

### 2. 启动 Java 后端

```bash
cd backend-java
mvn clean install -DskipTests
mvn spring-boot:run
```

## 工作流程

```
用户消息 → Java 后端 → Python AI 服务 → 智谱 AI API
                     ↓
            保存对话历史
                     ↓
            返回 AI 回复
```

## 技术特点

### 智谱 AI 集成
- 使用官方 SDK
- 流式输出（可选）
- Token 使用统计
- 错误重试机制

### 对话管理
- 完整对话历史
- 上下文保持
- 人设一致性

### 容错设计
- API 降级策略
- 异常处理
- 健康检查

## API 文档

### AI 服务 - 聊天生成

**Endpoint**: `POST /api/v1/ai/chat`

**Request**:
```json
{
  "systemPrompt": "你是一个温柔体贴的AI伴侣",
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好，我是你的AI伴侣"}
  ],
  "userMessage": "今天天气怎么样？"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Chat generated successfully",
  "data": {
    "content": "AI 回复内容",
    "usage": {
      "prompt_tokens": 100,
      "completion_tokens": 50
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### AI 服务 - 头像生成

**Endpoint**: `POST /api/v1/ai/generate-avatar`

**Request**:
```json
{
  "personality": "温柔体贴",
  "description": "可爱的动漫女孩"
}
```

## 模型选择

当前默认使用 `glm-4-flash`，您可以根据需要在 `.env` 文件中修改：

```bash
ZHIPU_MODEL=glm-4-flash
# 或者其他模型：
# ZHIPU_MODEL=glm-4
# ZHIPU_MODEL=glm-4-plus
```

## 注意事项

1. **API 密钥安全**: 请不要将 `.env` 文件提交到代码仓库
2. **Token 用量**: 注意智谱 AI 的 Token 使用量和费用
3. **服务依赖**: Java 后端依赖 Python AI 服务，需要按顺序启动
4. **网络连接**: 确保可以访问智谱 AI API
