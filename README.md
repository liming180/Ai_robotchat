# AI 情侣互动产品 (AI Companion)

一个温馨浪漫的 AI 陪伴聊天应用，采用现代前后端分离架构，基于 Vue 3 + FastAPI + GLM 大模型构建。

## 🌐 项目概述

AI 情侣互动产品是一个专注于情感陪伴的聊天应用，让用户可以与个性化的 AI 伴侣进行温馨浪漫的对话。应用采用动漫风格的视觉设计，支持自定义 AI 伴侣的性格、外貌和对话风格。

## 🏗️ 项目架构

### 技术栈

#### 前端技术栈
- **框架**: Vue 3 + Composition API
- **语言**: TypeScript
- **构建工具**: Vite 5
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **样式**: Tailwind CSS 3

#### 后端技术栈
- **Python AI 服务**：FastAPI + Uvicorn + SQLAlchemy 2.0 + LangChain 1.x + Redis（可选）+ 智谱 GLM（`glm-4.5-air` 文本 / `glm-4v-flash` 视觉 / `cogview-4` 图像）
- **Java 业务服务**：Spring Boot 3 + MyBatis Plus + MySQL 8 + Redis + JWT 双 Token
- **RAG 知识库**：FastAPI + Chroma + 本地哈希向量（256 维）

## 📁 项目结构

```
Ai_robotchat/
├── docs/                        # 项目文档
├── frontend/                    # Vue 3 前端（:3000）
├── backend/                     # Python AI 服务（:5000）
│   ├── app/ai/                  # LangChain / RAG / prompts / config
│   ├── app/services/            # 记忆/情绪 CRUD
│   ├── main.py                  # 单文件大入口（全部路由）
│   └── tests/                   # pytest
├── backend-java/                # Java 业务后端（:8081）
├── RAG-Knowledge-System/backend/# RAG 知识库服务（:8002）
├── scripts/                     # start-all.ps1 / stop-all.ps1
└── README.md
├── AI_design/                  # 设计资源
└── README.md
```

## 🚀 快速开始

### 环境要求

- **Node.js**: >= 18
- **Python**: >= 3.10
- **PostgreSQL**: >= 14
- **Redis**: >= 7

### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 开发环境启动 (默认端口 3000)
npm run dev

# 4. 生产环境构建
npm run build
```

### 后端启动

```bash
# ── Python AI 服务（:5000）──
cd backend
pip install -r requirements.txt
cp .env.example .env          # 填入 ZHIPU_API_KEY、SERVICE_TOKEN 等
python -m uvicorn main:app --host 0.0.0.0 --port 5000
# 注意：不要用 python main.py（APP_DEBUG=true 会开 reload，kill 后留孤儿进程占端口）

# ── Java 业务后端（:8081）──
cd backend-java
mvn clean install
mvn spring-boot:run           # 端口与上传地址已在 application.yml 固定为 8081

# ── RAG 知识库（:8002）──
cd RAG-Knowledge-System/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

> 便捷方式：`powershell -NoProfile -File scripts/start-all.ps1` 一并启动 3000 / 5000 / 8002（日志写入 `logs/`），`powershell -NoProfile -File scripts/stop-all.ps1` 全部停止（含 reload 孤儿子进程）。

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3000 |
| Java 业务 API | http://localhost:8081/api/v1 |
| Java Swagger | http://localhost:8081/doc.html |
| Python AI | http://localhost:5000 |
| Python API 文档 | http://localhost:5000/docs |
| RAG 知识库 | http://localhost:8002/docs |

## 📱 核心功能

### 已完成的前端页面
- ✅ 官网首页 - 产品介绍
- ✅ 登录/注册 - 用户认证
- ✅ AI 伴侣广场 - 浏览所有伴侣
- ✅ AI 伴侣创建 - 自定义创建
- ✅ 聊天页面 - 核心聊天功能
- ✅ AI 人设设置 - 个性化配置
- ✅ 聊天历史记录 - 历史对话
- ✅ 个人中心 - 用户管理

### 后端能力现状（2026-11-15）

任务零~任务七已完成：前端全部业务接 Java 8081、流式聊天 SSE + 落库、头像生成（Java 代理 + 落盘）、RAG 知识库收敛到 8002、流式端点共享密钥。剩余待办见 [docs/02-后端开发任务清单.md](docs/02-后端开发任务清单.md)。

## 🔐 环境变量配置

### Python AI 服务（`backend/.env`，模板见 `.env.example`）

```env
ZHIPU_API_KEY=sk-***
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4.5-air
ZHIPU_VISION_MODEL=glm-4v-flash
ZHIPU_IMAGE_MODEL=cogview-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024
LLM_TOP_P=0.9
DATABASE_URL=sqlite:///./ai_companion.db
REDIS_URL=redis://localhost:6379/1
APP_HOST=0.0.0.0
APP_PORT=5000
APP_DEBUG=true
SERVICE_TOKEN=            # 流式端点共享密钥；留空则不校验（仅本地开发）
```

### 前端（`frontend/.env.development`，模板见 `.env.example`）

```env
VITE_API_BASE_URL=http://localhost:8081
VITE_AI_BASE_URL=http://localhost:5000
VITE_SERVICE_TOKEN=       # 与后端 SERVICE_TOKEN 一致
```

### Java 业务后端（`backend-java/src/main/resources/application.yml`）

- MySQL / Redis 密码走用户级环境变量 `MYSQL_PASSWORD` / `REDIS_PASSWORD`（**必须新开终端启动 Java 才生效**）
- `server.port: 8081`、`app.upload.base-url: http://localhost:8081` 已在 yml 固定

### RAG 知识库（`RAG-Knowledge-System/backend/.env`，模板见 `.env.example`）

- `DATABASE_URL` 指向 MySQL `rag_knowledge` 库；`MAIN_DATABASE_URL` 指向 `ai_companion`（伴侣下拉用）
- 向量为本地哈希向量，**无需任何 API key**
- `ALLOWED_EXTENSIONS=json,md,txt`

## 📚 文档

- [架构设计文档](docs/01-项目架构设计文档.md) - 项目架构、目录结构、通信规范
- [后端开发任务清单](docs/02-后端开发任务清单.md) - 后端开发任务、里程碑、验收标准
- [API 接口文档](docs/03-API接口文档.md) - API 详细说明、请求示例、响应格式
- [收敛点清单](docs/04-重构接后端收敛点清单.md) - P0/P1/P2 收敛进度与待办
- [前后端打通落地计划](docs/superpowers/plans/2026-10-23-前后端打通与接后端落地.md) - 任务零~九实施记录

## 🤝 开发流程

1. **前端开发**: 先在 `frontend/` 目录下开发，可独立运行
2. **后端开发**: 按照任务清单在 `backend/` 目录下开发 API
3. **联调测试**: 完成后进行前后端联调
4. **提交代码**: 通过 PR 形式合并到主分支

## 📄 许可证

MIT License

## 💬 联系方式

如有问题或建议，欢迎联系！
