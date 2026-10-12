# AI 服务集成说明

## 概述

AI 服务采用**双模型架构**，按功能路由到两个 OpenAI 兼容平台：

| 链路 | 平台 | 模型 | 承担功能 |
| --- | --- | --- | --- |
| 文本链路 | 小米 MiMo | `mimo-v2.6-flash` | 对话、快捷建议、RAG、Function Calling |
| 视觉链路 | GPTCODEX 中转站 | `gpt-6-luna` | 图片理解（多模态） |
| 图像生成 | 无远程模型 | — | 本地 SVG 头像降级 |

两条链路均为 OpenAI 兼容协议，使用 `openai.OpenAI` 客户端；配置全部经环境变量注入（env 优先，代码不写死）。**密钥只存在于 `backend/.env`（已被 gitignore），本文档一律使用 `sk-***` 占位。**

## 架构

```
用户消息 ──► Python AI 服务 (backend/, 端口 5000)
                │
                ├─ 纯文本 ──► 文本链路 MiMo (mimo-v2.6-flash)
                │              └─ LangChain Agent（Function Calling + RAG）
                │
                ├─ 带图片 ──► 视觉链路 GPTCODEX (gpt-6-luna)
                │
                └─ 头像生成 ─► LLM_IMAGE_MODEL 置空 → 本地 SVG 降级
```

## 环境变量配置

配置文件位置：[backend/.env](file:///d:/Ai_robotchat/backend/.env)（复制 [backend/.env.example](file:///d:/Ai_robotchat/backend/.env.example) 后填入真实值）。

### 文本链路（小米 MiMo）

| 变量 | 示例值 | 说明 |
| --- | --- | --- |
| `LLM_MODEL_API_KEY` | `sk-***` | MiMo 平台密钥 |
| `LLM_MODEL_BASE_URL` | `https://api.xiaomimimo.com/v1` | OpenAI 兼容端点 |
| `LLM_MODEL_MODEL` | `mimo-v2.6-flash` | 文本模型 |

### 视觉链路（GPTCODEX 中转站）

| 变量 | 示例值 | 说明 |
| --- | --- | --- |
| `LLM_VISION_API_KEY` | `sk-***` | GPTCODEX 中转站密钥 |
| `LLM_VISION_BASE_URL` | `https://gptcodex.top/v1` | OpenAI 兼容端点 |
| `LLM_VISION_MODEL` | `gpt-6-luna` | 图片理解模型 |

### 图像生成与采样参数

| 变量 | 示例值 | 说明 |
| --- | --- | --- |
| `LLM_IMAGE_MODEL` | （空） | 置空触发本地 SVG 头像降级 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度（两链路共用） |
| `LLM_MAX_TOKENS` | `1024` | 最大输出 token |
| `LLM_TOP_P` | `0.9` | 核采样 |

## Python AI 服务

### 更新文件

- [backend/.env](file:///d:/Ai_robotchat/backend/.env) — 双链路变量
- [backend/main.py](file:///d:/Ai_robotchat/backend/main.py) — 双 `openai.OpenAI` 客户端，按 `images` 路由文本/视觉链路
- [backend/app/ai/config.py](file:///d:/Ai_robotchat/backend/app/ai/config.py) — `LLMConfig` 配置类（env 优先）
- [backend/app/ai/langchain_client.py](file:///d:/Ai_robotchat/backend/app/ai/langchain_client.py) — LangChain Agent（Function Calling + RAG）
- [backend/app/ai/rag.py](file:///d:/Ai_robotchat/backend/app/ai/rag.py) — RAG 知识库（本地哈希向量，两平台无 Embedding 端点）

### 主要功能

- 双客户端按功能路由（文本 / 视觉）
- 对话历史、系统提示词（伴侣人设）
- 普通对话关闭模型思考（`thinking: disabled`）以降低延迟；LangChain 链路保留思考以保证工具选择质量
- 完整降级链：LangChain Agent → OpenAI 直连 → 预设回复库

### 示例代码

```python
from openai import OpenAI

# 文本链路
llm = OpenAI(api_key="sk-***", base_url="https://api.xiaomimimo.com/v1")
resp = llm.chat.completions.create(
    model="mimo-v2.6-flash",
    messages=[{"role": "user", "content": "你好"}],
    max_completion_tokens=512,
    extra_body={"thinking": {"type": "disabled"}},  # 普通对话关思考降延迟
)

# 视觉链路（图片理解）
vision = OpenAI(api_key="sk-***", base_url="https://gptcodex.top/v1")
resp = vision.chat.completions.create(
    model="gpt-6-luna",
    messages=[{"role": "user", "content": [
        {"type": "text", "text": "描述这张图片"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
    ]}],
    max_completion_tokens=200,
)
```

## 启动步骤

### 1. 启动 AI 服务

```bash
cd backend
pip install -r requirements.txt
python main.py
```

访问健康检查接口验证：http://localhost:5000/health
（响应中 `llm_available` / `vision_available` 分别表示两条链路的初始化状态）

### 2. 启动 Java 后端

```bash
cd backend-java
mvn clean install -DskipTests
mvn spring-boot:run
```

## 工作流程

```
用户消息 → Java 后端 → Python AI 服务
                          ├─ 文本 ─► MiMo mimo-v2.6-flash
                          ├─ 图片 ─► GPTCODEX gpt-6-luna
                          └─ 头像 ─► 本地 SVG
                     ↓
            保存对话历史
                     ↓
            返回 AI 回复
```

## 容错设计

- **降级策略**：LangChain Agent → OpenAI 直连 → 预设回复库，任一层失败自动落到下一层
- **视觉缺失**：`LLM_VISION_API_KEY` 未配置时图片被丢弃并打印告警，对话不中断
- **图像生成**：`LLM_IMAGE_MODEL` 置空或远程调用失败时自动生成本地 SVG 头像
- **RAG**：Chroma 不可用时退化为内存检索；Embedding 使用本地哈希向量（两平台无 Embedding 端点）

## 注意事项

1. **API 密钥安全**: 密钥只写入 `.env`（gitignore 已忽略），不要提交到代码仓库或写入文档
2. **Token 用量**: 注意两个平台的 Token 使用量和费用
3. **服务依赖**: Java 后端依赖 Python AI 服务，需要按顺序启动
4. **网络连接**: 确保可以访问 `api.xiaomimimo.com` 与 `gptcodex.top`
