# AI Companion AI Service

基于 FastAPI 的 AI 服务，为 AI 伴侣应用提供聊天生成和头像生成功能。

## 技术栈

- **FastAPI** - Web 框架
- **Uvicorn** - ASGI 服务器
- **Pydantic** - 数据验证

## 快速开始

### 1. 环境要求

- Python 3.9+
- pip

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

或者使用 Uvicorn 直接运行：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### 4. 访问 API 文档

启动成功后，访问：`http://localhost:5000/docs`

## API 接口

### 健康检查

- `GET /health` - 健康检查
- `GET /` - 根路径

### AI 功能

- `POST /api/v1/ai/chat` - 生成聊天回复
- `POST /api/v1/ai/generate-avatar` - 生成头像

## 默认配置

- 服务端口：5000
- 地址：0.0.0.0

## 注意事项

- 当前为模拟实现，使用简单的回复逻辑
- 头像生成使用 DiceBear 公共 API
- 可以根据需要替换为真实的 LLM API（如 OpenAI、Claude、智谱 AI 等）
