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
- **Web 框架**: FastAPI
- **ASGI 服务器**: Uvicorn
- **ORM**: SQLAlchemy 2.0
- **数据库迁移**: Alembic
- **缓存**: Redis
- **身份认证**: JWT
- **AI 模型**: 智谱 GLM-4.5-Air
- **异步 HTTP 客户端**: httpx

## 📁 项目结构

```
Ai_robotchat/
├── docs/                        # 项目文档
│   ├── 01-项目架构设计文档.md      # 架构设计
│   ├── 02-后端开发任务清单.md      # 后端任务清单
│   └── 03-API接口文档.md          # API 文档
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── components/         # 公共组件
│   │   ├── composables/        # 组合式函数
│   │   ├── pages/             # 页面组件
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── types/             # TypeScript 类型
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── backend/                     # 后端项目
│   ├── app/
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic 验证模型
│   │   ├── api/               # API 路由
│   │   ├── services/          # 业务逻辑
│   │   ├── websockets/        # WebSocket 处理
│   │   └── utils/             # 工具函数
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py
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
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入数据库、Redis、GLM API 等配置

# 6. 启动服务 (默认端口 8000)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 访问地址

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

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

### 待开发的后端功能
详见 [docs/02-后端开发任务清单.md](docs/02-后端开发任务清单.md)

## 🔐 环境变量配置

### 后端环境变量 (.env)

```env
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/ai_companion

# Redis
REDIS_URL=redis://localhost:6379/1

# JWT
JWT_SECRET_KEY=your-super-secret-key

# GLM API
GLM_API_KEY=your-glm-api-key-here
GLM_MODEL=GLM-4.5-Air
```

## 📚 文档

- [架构设计文档](docs/01-项目架构设计文档.md) - 项目架构、目录结构、通信规范
- [后端开发任务清单](docs/02-后端开发任务清单.md) - 后端开发任务、里程碑、验收标准
- [API 接口文档](docs/03-API接口文档.md) - API 详细说明、请求示例、响应格式

## 🤝 开发流程

1. **前端开发**: 先在 `frontend/` 目录下开发，可独立运行
2. **后端开发**: 按照任务清单在 `backend/` 目录下开发 API
3. **联调测试**: 完成后进行前后端联调
4. **提交代码**: 通过 PR 形式合并到主分支

## 📄 许可证

MIT License

## 💬 联系方式

如有问题或建议，欢迎联系！
