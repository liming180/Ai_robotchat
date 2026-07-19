# AI 虚拟伙伴 · 头像与聊天升级设计

> 日期：2026-07-11  
> 范围：头像生成模块 + 智能聊天交互模块  
> 路线：升级智谱 GLM（基础款），聚焦 AI 质量，保持前端↔Python 直连

## 1. 背景与根因

三层架构：Vue3 前端 (3000) → Python FastAPI AI 服务 (5000) → 智谱 GLM。Java 后端 (8080) 已建但前端未接入，本次不动。

**根因（已实测确认）**：
- `backend/main.py` 依赖 `zhipuai` SDK，但运行环境（`D:\python\python.exe`）未安装该 SDK → `zhipu_client = None`
- `/health` 实测返回 `zhipu_available: false`
- 后果：聊天全降级为 `random.choice(3-5 条预设话术)`；头像全降级为 SVG 渐变 + 汉字。这就是"聊天机械化、头像差"的真凶——AI 根本没被调用。

**已验证可用**（httpx 直调 OpenAI 兼容端点，API Key 有效）：
- 聊天模型：`glm-4-flash`（基础款，本次采用）、`glm-4.6`、`glm-4-plus` 可选
- 文生图模型：`cogview-3`（基础款，本次采用）、`cogview-3-plus`、`cogview-4`、`cogview-3-flash` 可选
- 图片 URL 为临时地址且域名含 watermark → 必须服务端下载落盘

## 2. 模型选型（基础款，env 可配）

| 用途 | 模型 | env |
|------|------|-----|
| 聊天 | `glm-4-flash` | `ZHIPU_MODEL` |
| 头像 | `cogview-3` | `ZHIPU_IMAGE_MODEL` |

**关键改动**：弃用 `zhipuai` SDK，改用 `httpx` 直调 `https://open.bigmodel.cn/api/paas/v4/`（环境已装 httpx），消除 SDK 依赖脆弱性。

## 3. 模块一：头像生成（高质感动漫头像）

### 3.1 结构化提示词（替代一句话）
```
{画风锁定词} + {风格预设} + {人物设定：性别/发色/瞳色/服装} + {性格气质} + {构图：半身} + {画质词}
```
- 画风锁定词固定前缀（如"高质量日系赛璐璐动漫插画、柔和光影、精致五官、纯色背景"）→ 保证同一伴侣多次生成风格统一
- 风格预设：日系治愈 / 国风古韵 / 赛博朋克 / 水彩柔彩 / Q版萌系
- 可定制输入：性别、发色、瞳色、服装关键词、性格（来自伴侣设定）、描述

### 3.2 服务端持久化（解决 localStorage 5MB 配额）
- 生成后 Python 用 httpx 下载图片 → 存 `backend/static/avatars/{uuid}.png`
- FastAPI 挂载 `/static` 静态目录 → 返回稳定 URL `http://localhost:5000/static/avatars/{uuid}.png`
- 前端只存 URL 字符串，不再存 base64 data URL → 彻底解决配额溢出
- 支持"重新生成"产出不同变体

### 3.3 接口
`POST /api/v1/ai/generate-avatar`
```json
// 请求（兼容旧字段，新增可选）
{ "personality": "温柔体贴", "description": "...",
  "style": "anime_healing", "gender": "female",
  "hairColor": "", "eyeColor": "", "outfit": "" }
// 响应
{ "success": true, "data": { "avatarUrl": "http://localhost:5000/static/avatars/xxx.png" } }
```

## 4. 模块二：智能聊天（情感陪伴 + 实用咨询）

### 4.1 多层系统提示词（替代一句话）
1. **人设层**：名字/性格/说话风格（来自伴侣 systemPrompt）
2. **共情层**：识别用户情绪 → 共情回应 → 情绪疏导 → 积极正向引导（四步法）
3. **实用层**：知识/事实问题严谨准确、分点清晰、不编造、不确定时坦诚说明
4. **平衡规则**：日常闲聊偏情感陪伴；提问类偏实用解答；自动判断切换
5. **安全底线**：不输出有害内容；遇自伤/危机信号给出专业求助渠道

### 4.2 流式输出（SSE）
- 新增 `POST /api/v1/ai/chat/stream`，`text/event-stream` 逐 token 返回
- 保留 `POST /api/v1/ai/chat`（非流式）兼容旧调用
- 前端 ChatPage 改为 SSE 读取 → 打字机逐字渲染

### 4.3 对话历史与降级
- 前端发最近 10 轮；Python 端角色归一化 + 去空 + 末尾追加当前 userMessage
- API 失败时降级：按场景（问候/负面情绪/知识提问）选预设，比随机话术得体

### 4.4 参数
`temperature=0.8`（略高于原 0.7，更自然有温度），`max_tokens=1024`，`top_p=0.9`

## 5. 前端改造

- `src/lib/ai.ts`（新增）：封装 SSE 流式读取 + 头像生成 API，替代裸 fetch
- `src/pages/ChatPage.vue`：`fetch`→SSE 逐字渲染，保留打字动画与降级
- `src/pages/CreatePage.vue`：新增风格/性别/视觉特征选择器，调用新头像接口
- `src/stores/companion.ts`：头像只存 URL（SVG 仅作加载失败兜底）
- `src/lib/avatar.ts`：保留 SVG 兜底

## 6. 代码结构（Python）

```
backend/
├── app/ai/
│   ├── __init__.py
│   ├── glm_client.py     # httpx 直调 GLM：chat/chat_stream/generate_image
│   ├── prompts.py        # 系统提示词构建 + 头像提示词构建
│   └── avatar_store.py   # 图片下载落盘 + 静态服务
├── tests/
│   ├── test_prompts.py
│   └── test_avatar_store.py
└── main.py               # 薄路由层
```

## 7. 测试（上线前）

1. 单元：提示词构建、头像落盘、历史截断/角色归一化（pytest）
2. 端到端（全栈已运行）：
   - 5 种头像风格各出图 + 持久化 URL 可访问
   - 情感类问题（"我今天好难过"）→ 共情疏导回复
   - 实用类问题（"解释量子纠缠"）→ 准确分点解答
   - 流式逐字输出
   - API 失败降级
   - 前端 localStorage 不再因头像溢出
