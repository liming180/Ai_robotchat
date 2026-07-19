# AI 情侣互动产品 - API 接口文档

## 📋 文档信息

| 项目名称 | AI 情侣互动产品 API |
|---------|---------------------|
| API 版本 | v1 |
| 最后更新 | 2026-07-11 |
| 后端基础 URL | `http://localhost:8080/api/v1` |
| AI 服务基础 URL | `http://localhost:5000/api/v1` |

---

## 🔐 认证说明

### 认证方式：JWT Bearer Token

所有需要认证的接口都需要在 Header 中携带 Token：

```
Authorization: Bearer {access_token}
```

### 获取 Token

通过登录接口获取，详见 [登录接口](#登录接口)。

---

## 🔌 接口总览

| 模块 | 接口数量 | 说明 |
|------|----------|------|
| 认证模块 | 5 | 发送邮箱验证码、邮箱登录、邮箱注册、验证邮箱验证码、刷新 Token |
| 用户模块 | 3 | 用户信息查询、更新 |
| 伴侣模块 | 7 | 伴侣列表、详情、创建、收藏等 |
| 聊天模块 | 6 | 对话管理、消息发送 |
| AI 模块 | 2 | 头像生成等 AI 能力 |

---

## 🔓 认证模块 (Auth)

### 1. 发送邮箱验证码

**接口**：`POST /api/v1/auth/send-email-code`

**请求参数**：
```json
{
  "email": "user@example.com"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "验证码发送成功",
  "data": {
    "sent": true,
    "expiresIn": 300
  },
  "timestamp": "2026-07-11T12:00:00Z"
}
```

---

### 2. 验证邮箱验证码

**接口**：`POST /api/v1/auth/verify-email-code`

**请求参数**：
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "验证码验证成功",
  "data": {
    "verified": true
  },
  "timestamp": "2026-07-11T12:00:00Z"
}
```

---

### 3. 用户注册（设置密码）

**接口**：`POST /api/v1/auth/register`

**请求参数**：
```json
{
  "email": "user@example.com",
  "code": "123456",
  "name": "用户名",
  "password": "password123"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "用户名",
      "avatar": null
    }
  },
  "timestamp": "2026-07-11T12:00:00Z"
}
```

---

### 4. 用户登录

**接口**：`POST /api/v1/auth/login`

**请求参数**：
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "用户名",
      "avatar": null
    }
  },
  "timestamp": "2026-07-11T12:00:00Z"
}
```

---

### 5. 刷新 Token

**接口**：`POST /api/v1/auth/refresh`

**请求参数**：
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "access_token": "new-access-token...",
    "token_type": "bearer"
  },
  "message": "刷新成功"
}
```

---

## 👤 用户模块 (Users)

### 1. 获取当前用户信息

**接口**：`GET /api/v1/users/me`

**认证**：需要

**响应**：
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "用户名",
    "avatar": "https://example.com/avatar.jpg",
    "created_at": "2026-07-10T12:00:00Z"
  },
  "message": "获取成功"
}
```

---

### 2. 更新用户信息

**接口**：`PUT /api/v1/users/me`

**认证**：需要

**请求参数**：
```json
{
  "name": "新用户名",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

**响应**：
```json
{
  "success": true,
  "data": { /* 更新后的用户信息 */ },
  "message": "更新成功"
}
```

---

## 💖 伴侣模块 (Companions)

### 1. 获取伴侣列表

**接口**：`GET /api/v1/companions`

**认证**：需要

**Query 参数**：
- `category`: 分类筛选 (可选，如 "日常聊天")
- `search`: 搜索关键词 (可选)
- `favorite`: 是否只返回收藏 (true/false，可选)

**响应**：
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-1",
      "name": "小暖",
      "avatar": "https://api.dicebear.com/...",
      "description": "温柔体贴的聊天伙伴",
      "category": "日常聊天",
      "personality": "温柔体贴",
      "is_favorite": true,
      "intimacy": 0,
      "tags": ["温柔", "倾听"]
    }
  ],
  "message": "获取成功"
}
```

---

### 2. 获取伴侣详情

**接口**：`GET /api/v1/companions/{id}`

**认证**：需要

**响应**：
```json
{
  "success": true,
  "data": {
    "id": "uuid-1",
    "name": "小暖",
    "avatar": "https://api.dicebear.com/...",
    "description": "温柔体贴的聊天伙伴",
    "category": "日常聊天",
    "personality": "温柔体贴",
    "system_prompt": "你是一个温柔体贴的AI伴侣...",
    "is_favorite": true,
    "intimacy": 0,
    "tags": ["温柔", "倾听"],
    "created_at": "2026-07-10T12:00:00Z"
  },
  "message": "获取成功"
}
```

---

### 3. 创建自定义伴侣

**接口**：`POST /api/v1/companions`

**认证**：需要

**请求参数**：
```json
{
  "name": "我的专属伴侣",
  "avatar": "https://example.com/avatar.jpg",
  "description": "这是我的专属伴侣",
  "category": "日常聊天",
  "personality": "温柔体贴",
  "system_prompt": "你是我的专属AI伴侣...",
  "tags": ["温柔", "专属"]
}
```

**响应**：
```json
{
  "success": true,
  "data": { /* 创建的伴侣信息 */ },
  "message": "创建成功"
}
```

---

### 4. 更新伴侣人设

**接口**：`PUT /api/v1/companions/{id}`

**认证**：需要 (只能更新自己创建的伴侣)

**请求参数**：
```json
{
  "name": "新名字",
  "avatar": "new-avatar-url",
  "description": "新描述",
  "personality": "新性格",
  "system_prompt": "新的系统提示词"
}
```

---

### 5. 切换收藏状态

**接口**：`PATCH /api/v1/companions/{id}/favorite`

**认证**：需要

**响应**：
```json
{
  "success": true,
  "data": {
    "is_favorite": true
  },
  "message": "操作成功"
}
```

---

### 6. 增加亲密度

**接口**：`PATCH /api/v1/companions/{id}/intimacy`

**认证**：需要

**请求参数**：
```json
{
  "amount": 5
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "intimacy": 25
  },
  "message": "亲密度增加成功"
}
```

---

## 💬 聊天模块 (Chat)

### 1. 获取对话列表

**接口**：`GET /api/v1/chat/conversations`

**认证**：需要

**Query 参数**：
- `companion_id`: 伴侣 ID (可选，筛选特定伴侣的对话)
- `page`: 页码 (默认 1)
- `page_size`: 每页数量 (默认 20)

**响应**：
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "conv-1",
        "companion_id": "uuid-1",
        "title": "今天的心情如何",
        "last_message": "我今天很开心...",
        "updated_at": "2026-07-10T15:30:00Z"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  },
  "message": "获取成功"
}
```

---

### 2. 创建新对话

**接口**：`POST /api/v1/chat/conversations`

**认证**：需要

**请求参数**：
```json
{
  "companion_id": "uuid-1",
  "title": "新对话"
}
```

---

### 3. 获取对话详情

**接口**：`GET /api/v1/chat/conversations/{id}`

**认证**：需要

**响应**：
```json
{
  "success": true,
  "data": {
    "id": "conv-1",
    "title": "今天的心情如何",
    "companion": { /* 伴侣信息 */ },
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "你好",
        "timestamp": "2026-07-10T15:30:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "你好！我是小暖...",
        "timestamp": "2026-07-10T15:30:01Z"
      }
    ]
  },
  "message": "获取成功"
}
```

---

### 4. 发送消息 (REST)

**接口**：`POST /api/v1/chat/conversations/{id}/messages`

**认证**：需要

**请求参数**：
```json
{
  "content": "你好，今天怎么样？"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": "msg-3",
      "role": "user",
      "content": "你好，今天怎么样？",
      "timestamp": "2026-07-10T15:35:00Z"
    },
    "ai_message": {
      "id": "msg-4",
      "role": "assistant",
      "content": "我很好，谢谢关心！你呢？",
      "timestamp": "2026-07-10T15:35:01Z"
    }
  },
  "message": "发送成功"
}
```

---

### 5. 删除对话

**接口**：`DELETE /api/v1/chat/conversations/{id}`

**认证**：需要

---

## 🤖 AI 模块 (AI)

### 1. AI 生成头像

**接口**：`POST /api/v1/ai/generate-avatar`

**认证**：需要

**请求参数**：
```json
{
  "personality": "温柔体贴",
  "description": "可爱的动漫女孩，粉色头发"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "avatar_url": "https://cdn.example.com/generated-avatar-xxxxx.jpg"
  },
  "message": "生成成功"
}
```

---

## 🔌 WebSocket 实时聊天

### 连接 URL

```
ws://localhost:8000/api/v1/chat/ws/{conversation_id}?token={access_token}
```

### 消息格式

#### 发送消息 (客户端 -> 服务端)

```json
{
  "type": "send_message",
  "data": {
    "content": "你好"
  }
}
```

#### 接收消息 (服务端 -> 客户端)

```json
{
  "type": "new_message",
  "data": {
    "role": "assistant",
    "content": "你好！我是小暖",
    "timestamp": "2026-07-10T15:30:00Z"
  }
}
```

#### 正在输入 (服务端 -> 客户端)

```json
{
  "type": "typing",
  "data": {
    "is_typing": true
  }
}
```

---

## 📦 统一响应格式

### Java 后端统一响应格式

所有 API 响应遵循统一格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { /* 响应数据 */ },
  "timestamp": "2026-07-11T12:00:00Z"
}
```

### 响应码规范

| code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## ⚠️ 错误响应格式

```json
{
  "code": 400,
  "message": "错误描述",
  "data": null,
  "timestamp": "2026-07-11T12:00:00Z"
}
```

### 常见错误码

| code | message | 说明 |
|------|---------|------|
| 400 | VALIDATION_ERROR | 参数验证失败 |
| 401 | UNAUTHORIZED | 未登录或 Token 过期 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | ALREADY_EXISTS | 资源已存在 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 🤖 Python AI 服务 API（Java 后端内部调用）

### 1. 聊天生成接口

**接口**：`POST /api/v1/ai/chat`

**请求参数**：
```json
{
  "systemPrompt": "你是一个温柔体贴的AI伴侣...",
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！我是你的AI伴侣..."}
  ],
  "userMessage": "今天天气怎么样？"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "content": "今天天气很不错，适合出去走走呢！",
    "usage": {
      "promptTokens": 100,
      "completionTokens": 50
    }
  }
}
```

### 2. 头像生成接口

**接口**：`POST /api/v1/ai/generate-avatar`

**请求参数**：
```json
{
  "personality": "温柔体贴",
  "description": "可爱的动漫女孩，粉色头发"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "avatarUrl": "https://cdn.example.com/generated-avatar-xxxxx.jpg"
  }
}
```

---

*文档结束*
