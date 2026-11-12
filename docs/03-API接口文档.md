# AI 伴侣应用 - API 接口文档

## 📋 文档信息

| 项目名称 | AI 伴侣应用 API |
|---------|-----------------|
| API 版本 | v1 |
| 最后更新 | 2026-10-23 |
| Java 业务后端 | `http://localhost:8080/api/v1` |
| Python AI 服务 | `http://localhost:5000` |
| RAG 知识库服务 | `http://localhost:8002/api/v1/kb` |

> **本版按实际代码重写**（`backend-java/src` 与 `backend/main.py` 逐接口核对）。
> 与旧版差异：删除不存在的 `/auth/verify-email-code` 与 WebSocket 章节；全部字段改 camelCase（与实际 DTO 一致）；对话列表为纯数组（无 items/total 分页包装）；补充 Python AI 服务的流式/建议/记忆/心情接口。

---

## 📦 统一响应格式（两套，注意区分）

### Java 业务后端（8080）

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { },
  "timestamp": "2026-10-23T12:00:00"
}
```

| code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未认证 / Token 过期 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### Python AI 服务（5000）

```json
{
  "success": true,
  "message": "Chat generated successfully",
  "data": { },
  "timestamp": "2026-10-23T12:00:00"
}
```

**命名规范**：JSON 一律 camelCase；数据库列为 snake_case（不暴露到接口）。

---

## 🔐 认证说明

Java 业务接口（除 `POST /api/v1/auth/*` 外）需要携带 Token：

```
Authorization: Bearer {accessToken}
```

Token 有效期：accessToken 2 小时、refreshToken 7 天。过期后用 `POST /api/v1/auth/refresh` 换新。

Python AI 服务当前**无鉴权**（收敛计划：加 `X-Service-Token` 共享密钥，见 [04-收敛点清单](./04-重构接后端收敛点清单.md) P1-5）。

---

## 🔓 认证模块 (Auth) — Java 8080

### 1. 发送邮箱验证码

`POST /api/v1/auth/send-email-code`（无需认证）

```json
// 请求
{ "email": "user@example.com" }
// 响应 data
{ "sent": true, "expiresIn": 300 }
```

### 2. 用户注册

`POST /api/v1/auth/register`（无需认证）

```json
// 请求
{
  "email": "user@example.com",
  "code": "123456",
  "name": "用户名",
  "password": "password123"
}
// 响应 data（AuthResponse）
{
  "accessToken": "eyJhbGciOi...",
  "refreshToken": "eyJhbGciOi...",
  "tokenType": "bearer",
  "user": { "id": "uuid", "email": "user@example.com", "name": "用户名", "avatar": null }
}
```

### 3. 用户登录

`POST /api/v1/auth/login`（无需认证）

```json
// 请求
{ "email": "user@example.com", "password": "password123" }
// 响应 data：同注册（AuthResponse）
```

### 4. 刷新 Token

`POST /api/v1/auth/refresh`（无需认证）

```json
// 请求
{ "refreshToken": "eyJhbGciOi..." }
// 响应 data：完整 AuthResponse（含新双 Token 与 user）
```

> 旧文档中的 `POST /api/v1/auth/verify-email-code` **不存在**，验证码在 register 时一并校验。

---

## 👤 用户模块 (Users) — Java 8080

### 1. 获取当前用户信息

`GET /api/v1/users/me`

```json
// 响应 data（AuthResponse.UserInfo）
{ "id": "uuid", "email": "user@example.com", "name": "用户名", "avatar": "https://..." }
```

### 2. 更新当前用户信息

`PUT /api/v1/users/me`

```json
// 请求（两字段均可选）
{ "name": "新用户名", "avatar": "https://..." }
// 响应 data：更新后的 UserInfo
```

---

## 💖 伴侣模块 (Companions) — Java 8080

`CompanionResponse` 结构（列表与详情一致）：

```json
{
  "id": "uuid",
  "name": "小暖",
  "avatar": "https://api.dicebear.com/...",
  "description": "温柔体贴的聊天伙伴",
  "category": "日常聊天",
  "personality": "温柔体贴",
  "systemPrompt": "你是一个温柔体贴的AI伴侣...",
  "isFavorite": false,
  "intimacy": 0,
  "tags": "温柔,倾听,陪伴",
  "createdAt": "2026-10-23T12:00:00"
}
```

> ⚠️ `tags` 实际是**逗号分隔字符串**（DB `VARCHAR(500)`），非数组，前端自行 split。
> `isPreset` 不在响应 DTO 中；预置伴侣由后端 `schema.sql` 初始化（preset-1~4：小暖/小智/小甜/小酷）。

### 1. 获取伴侣列表

`GET /api/v1/companions`

Query 参数（均可选）：`category` 分类、`search` 关键词、`favorite=true` 只看收藏。

```json
// 响应 data：CompanionResponse[]（纯数组，无分页包装）
[ { "id": "preset-1", "name": "小暖", "...": "..." } ]
```

### 2. 获取伴侣详情

`GET /api/v1/companions/{id}` → data 为 CompanionResponse。

### 3. 创建自定义伴侣

`POST /api/v1/companions`

```json
// 请求（name 必填）
{
  "name": "我的专属伴侣",
  "avatar": "https://...",
  "description": "描述",
  "category": "日常聊天",
  "personality": "温柔体贴",
  "systemPrompt": "你是我的专属AI伴侣...",
  "tags": "温柔,专属"
}
// 响应 data：创建的 CompanionResponse
```

### 4. 更新伴侣人设

`PUT /api/v1/companions/{id}` — 请求体同创建；只能更新自己创建的伴侣。

### 5. 切换收藏状态

`PATCH /api/v1/companions/{id}/favorite`（无请求体）

```json
// 响应 data
{ "isFavorite": true }
```

### 6. 增加亲密度

`PATCH /api/v1/companions/{id}/intimacy`

```json
// 请求
{ "amount": 5 }        // 缺省 1
// 响应 data
{ "intimacy": 25 }
```

---

## 💬 聊天模块 (Chat) — Java 8080

### 1. 获取对话列表

`GET /api/v1/chat/conversations`

Query 参数：`companionId`（可选）、`page`（默认 1）、`pageSize`（默认 20）。

```json
// 响应 data：ConversationResponse[]（纯数组；分页参数已被后端使用但不返回 total）
[
  {
    "id": "conv-uuid",
    "companionId": "preset-1",
    "title": "今天的心情如何",
    "updatedAt": "2026-10-23T15:30:00"
  }
]
```

### 2. 创建新对话

`POST /api/v1/chat/conversations`

```json
// 请求
{ "companionId": "preset-1", "title": "新对话" }   // title 可选，默认"新对话"
// 响应 data：ConversationResponse
```

### 3. 获取对话详情

`GET /api/v1/chat/conversations/{id}`

```json
// 响应 data（ConversationDetailResponse）
{
  "id": "conv-uuid",
  "title": "今天的心情如何",
  "companion": { "…": "CompanionResponse 完整结构" },
  "messages": [
    { "id": "msg-1", "role": "user", "content": "你好", "createdAt": "2026-10-23T15:30:00" },
    { "id": "msg-2", "role": "assistant", "content": "你好！我是小暖…", "createdAt": "2026-10-23T15:30:01" }
  ]
}
```

### 4. 发送消息 (REST，非流式)

`POST /api/v1/chat/conversations/{id}/messages`

```json
// 请求
{ "content": "你好，今天怎么样？" }
// 响应 data
{
  "userMessage": { "id": "msg-3", "role": "user", "content": "你好…", "createdAt": "…" },
  "aiMessage":   { "id": "msg-4", "role": "assistant", "content": "我很好…", "createdAt": "…" }
}
```

> **行为说明**：该接口会先落库用户消息，再由 Java 调用 Python `POST /api/v1/ai/chat`（非流式）生成回复并落库、亲密度 +1；AI 不可用时回复固定文案「抱歉，AI 服务暂时不可用。」。
> **前端当前并未使用此接口**——聊天走 Python SSE 流式（见下文 Python 端），落库方案在收敛计划任务六中改造（`generate=false` 纯落库模式）。

### 5. 删除对话

`DELETE /api/v1/chat/conversations/{id}` → `data: null`（逻辑删除对话及其消息）。

---

## 🤖 AI 模块 (Java) — 8080

### 生成伴侣头像

`POST /api/v1/ai/generate-avatar`

```json
// 请求
{ "personality": "温柔体贴", "description": "可爱的动漫女孩，粉色头发" }
// 响应 data
{ "avatarUrl": "https://api.dicebear.com/9.x/adventurer/svg?seed=..." }
```

> ⚠️ **现状**：Java 端 `AIServiceImpl` 直接拼 dicebear URL 返回，并未调用 Python。真实 AI 生成在 Python 端（见下），收敛计划任务五将改为 Java 代理 Python。

---

## 🤖 Python AI 服务 API — 5000

响应格式统一为 `{success, message, data, timestamp}`（流式接口除外）。

### 1. 健康检查

`GET /health`

```json
// data
{
  "status": "ok",
  "timestamp": "2026-10-23T12:00:00",
  "llm_available": true,
  "vision_available": true,
  "model": "mimo-v2.6-flash",
  "vision_model": "gpt-6-luna",
  "image_model": null
}
```

### 2. 聊天（非流式）

`POST /api/v1/ai/chat`

```json
// 请求（ChatRequest）
{
  "systemPrompt": "你是一个温柔体贴的AI伴侣…",
  "messages": [ { "role": "user", "content": "你好", "images": null } ],
  "userMessage": "今天天气怎么样？",
  "images": ["data:image/png;base64,..."],   // 可选，当前轮图片（base64 data URL）
  "userId": "user-uuid"                       // 可选，记忆/心情查询用
}
// 响应 data
{ "content": "今天天气很不错…", "usage": { "promptTokens": 100, "completionTokens": 50 } }
```

### 3. 聊天（SSE 流式）

`POST /api/v1/ai/chat/stream` — `Content-Type: application/json`，响应 `text/event-stream`。

请求体同上。事件格式：

```
data: {"delta": "今", "done": false}

data: {"delta": "天天气…", "done": false}

data: {"delta": "", "done": true}
```

> 图片路由：请求含 `images` 时走视觉模型（gpt-6-luna），否则走文本模型（mimo-v2.6-flash）。
> 三层降级：LLM 直连 → … → 预设回复库（`PRESET_RESPONSES`，按性格随机）。

### 4. LangChain 增强聊天（非流式）

`POST /api/v1/ai/chat/langchain`

请求体同 `/api/v1/ai/chat`。响应 data：

```json
{ "content": "…", "engine": "langchain" }   // 降级时 engine: "fallback"
```

工具：`web_search`、`search_user_memory`、`add_user_memory`、`get_mood_history`、`search_knowledge`。

### 5. LangChain 增强聊天（SSE 流式）

`POST /api/v1/ai/chat/langchain/stream` — 事件格式同第 3 节。

> ⚠️ **现状**：LangChain 链路的流式是**模拟流式**——Agent 一次性生成完毕后按块切分下发，首字延迟 ≈ 全量生成时间；普通 `/chat/stream` 为真流式。

### 6. 快捷回复建议

`POST /api/v1/ai/suggestions`

```json
// 请求
{ "systemPrompt": "…", "messages": [ { "role": "user", "content": "你好" } ] }
// 响应 data
{ "suggestions": ["你好呀 👋", "今天过得怎么样？", "给我讲个笑话 😄", "陪我聊聊天"] }
```

### 7. 生成头像（真 AI）

`POST /api/v1/ai/generate-avatar`

```json
// 请求
{ "personality": "温柔体贴", "description": "可爱的动漫女孩" }
// 响应 data
{ "avatarUrl": "https://…" }   // message 含 "using AI" 表示走远程图像模型；
                                // LLM_IMAGE_MODEL 未配置或失败时降级为本地 SVG data URL
```

### 8. 用户记忆

- `GET /api/v1/memory/{user_id}?keyword=xxx` → data `{ "memories": [{ "id", "userId", "type", "keyword", "content", "createdAt" }] }`
- `POST /api/v1/memory` → 请求 `{ "userId", "memoryType": "fact", "keyword": "可选", "content" }`，data 为单条记忆

> ⚠️ **现状**：查不到数据时返回示例假数据（收敛清单 P1-2 待清理）；数据库未配置返回 503。

### 9. 用户心情

- `GET /api/v1/mood/{user_id}?days=7` → data `{ "moods": [{ "id", "userId", "mood", "score", "note", "createdAt" }] }`
- `POST /api/v1/mood` → 请求 `{ "userId", "mood": "happy", "score": 8.5, "note": "可选" }`

> 同上，无数据时返回示例假数据（待清理）。

### 10. 性能指标

`GET /api/v1/metrics` → data `{ "operations": { "chat": { "count", "avg_ms", "min_ms", "max_ms", "p95_ms" } }, "redis_available": true }`

---

## 🔎 RAG 知识库服务 — 8002

前缀 `/api/v1/kb`，主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/kb/retrieve` | 检索，body 支持 `{query, collectionIds}` 或 `{query, companionId}` |
| — | 集合/文档/任务接口 | 见 `RAG-Knowledge-System/backend/app/api/v1/`（collections/documents/tasks） |

> **现状**：前端与主后端均未调用 8002；Python 主服务 `search_knowledge` 用的是自带的 `backend/app/ai/rag.py` 本地向量库（另一套数据）。收敛计划任务七将主服务改为优先代理 8002。

---

## 🚫 已移除/不采用的接口（历史说明）

| 旧文档内容 | 结论 |
|-----------|------|
| `POST /api/v1/auth/verify-email-code` | 不存在，验证码在注册时校验 |
| `ws://…/api/v1/chat/ws/{conversation_id}` | **不采用 WebSocket**；聊天走 Python SSE + 落库（Java 的 WebSocketConfig 为预留配置，无业务端点） |
| 对话列表 `data.items/total` 分页包装 | 实际返回纯数组 |
| snake_case 字段（`access_token`、`system_prompt`、`is_favorite` 等） | 实际全部 camelCase |

---

*文档结束（依据 2026-10-23 代码勘察重写）*
