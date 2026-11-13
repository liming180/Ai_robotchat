# AI 服务集成说明

## 概述

AI 服务采用**智谱 GLM 单平台三链路**架构，三条链路共用同一套 OpenAI 兼容端点：

| 链路 | 平台 | 模型 | 承担功能 |
| --- | --- | --- | --- |
| 文本链路 | 智谱 GLM | `glm-4.5-air` | 对话、快捷建议、RAG、Function Calling |
| 视觉链路 | 智谱 GLM | `glm-4v-flash` | 图片理解（多模态） |
| 图像生成 | 智谱 CogView | `cogview-4` | AI 头像生成 |

三条链路均为 OpenAI 兼容协议，使用 `openai.OpenAI` 客户端，base URL 统一为 `https://open.bigmodel.cn/api/paas/v4`；配置全部经环境变量注入（env 优先，代码不写死）。**密钥只存在于 `backend/.env`（已被 gitignore），本文档一律使用 `sk-***` 占位。**

## 架构

```
用户消息 ──► Python AI 服务 (backend/, 端口 5000)
                │
                ├─ 纯文本 ──► 文本链路 glm-4.5-air
                │              └─ LangChain Agent（Function Calling + RAG）
                │
                ├─ 带图片 ──► 视觉链路 glm-4v-flash
                │              （绕过 Agent 直连：Agent 的 HumanMessage 无法承载 image_url）
                │
                └─ 头像生成 ─► CogView cogview-4；置空或失败 → 本地 SVG 降级
```

## 环境变量配置

配置文件位置：[backend/.env](file:///d:/Ai_robotchat/backend/.env)（复制 [backend/.env.example](file:///d:/Ai_robotchat/backend/.env.example) 后填入真实值）。

### 智谱 GLM（文本 + 视觉共用同一个 key）

| 变量 | 示例值 | 说明 |
| --- | --- | --- |
| `ZHIPU_API_KEY` | `sk-***` | 智谱 API 密钥（三条链路共用） |
| `ZHIPU_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | OpenAI 兼容端点 |
| `ZHIPU_MODEL` | `glm-4.5-air` | 文本模型 |
| `ZHIPU_VISION_MODEL` | `glm-4v-flash` | 图片理解模型 |
| `ZHIPU_VISION_API_KEY` | （可选） | 视觉/图像走别的账号时才配置，默认复用 `ZHIPU_API_KEY` |

### 图像生成与采样参数

| 变量 | 示例值 | 说明 |
| --- | --- | --- |
| `ZHIPU_IMAGE_MODEL` | `cogview-4` | 图像生成模型；置空触发本地 SVG 头像降级 |
| `LLM_TEMPERATURE` | `0.7` | 采样温度（文本链路） |
| `LLM_MAX_TOKENS` | `1024` | 最大输出 token |
| `LLM_TOP_P` | `0.9` | 核采样 |

> 实测（2026-11-13）：`cogview-4` / `cogview-3-flash` / `cogview-3` 均可用，1024×1024 出图约 7.3–7.6 秒，取 `cogview-4`。

## Python AI 服务

### 更新文件

- [backend/.env](file:///d:/Ai_robotchat/backend/.env) — `ZHIPU_*` 变量
- [backend/main.py](file:///d:/Ai_robotchat/backend/main.py) — 双 `openai.OpenAI` 客户端，按 `images` 路由文本/视觉链路；头像走 `images.generate`
- [backend/app/ai/config.py](file:///d:/Ai_robotchat/backend/app/ai/config.py) — `LLMConfig` 配置类（字段映射自 `ZHIPU_*`，env 优先）
- [backend/app/ai/langchain_client.py](file:///d:/Ai_robotchat/backend/app/ai/langchain_client.py) — LangChain Agent（Function Calling + RAG）
- [backend/app/ai/rag.py](file:///d:/Ai_robotchat/backend/app/ai/rag.py) — RAG 知识库（本地哈希向量，未接入远程 Embedding API）

### 主要功能

- 双客户端按功能路由（文本 / 视觉）
- 对话历史、系统提示词（伴侣人设）
- **普通对话必须关闭模型思考**（`extra_body={"thinking": {"type": "disabled"}}`）：`glm-4.5-air` 是思考模型，不关时 `max_tokens` 较小时 `content` 会为空、内容全进 `reasoning_content`。LangChain 链路保留思考以保证工具选择质量
- 完整降级链：LangChain Agent → OpenAI 直连 → 预设回复库

### 示例代码

```python
from openai import OpenAI

# 文本链路
llm = OpenAI(api_key="sk-***", base_url="https://open.bigmodel.cn/api/paas/v4")
resp = llm.chat.completions.create(
    model="glm-4.5-air",
    messages=[{"role": "user", "content": "你好"}],
    max_completion_tokens=512,
    extra_body={"thinking": {"type": "disabled"}},  # 思考模型必须关思考
)

# 视觉链路（图片理解，与文本共用 key）
resp = llm.chat.completions.create(
    model="glm-4v-flash",
    messages=[{"role": "user", "content": [
        {"type": "text", "text": "描述这张图片"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
    ]}],
    max_completion_tokens=200,
)

# 图像生成（CogView）
img = llm.images.generate(
    model="cogview-4",
    prompt="可爱的动漫风格头像，温柔体贴，高清",
    size="1024x1024",
)
avatar_url = img.data[0].url
```

## 启动步骤

### 1. 启动 AI 服务

```bash
cd backend
pip install -r requirements.txt
python main.py
```

访问健康检查接口验证：http://localhost:5000/health
（响应中 `llm_available` / `vision_available` 表示链路初始化状态，`model` / `vision_model` / `image_model` 为实际生效的模型名）

### 2. 启动 Java 后端

```bash
cd backend-java
mvn clean install -DskipTests
mvn spring-boot:run
```

## 工作流程

```
用户消息 → Java 后端 → Python AI 服务
                          ├─ 文本 ─► GLM glm-4.5-air
                          ├─ 图片 ─► GLM glm-4v-flash
                          └─ 头像 ─► CogView cogview-4（失败则本地 SVG）
                     ↓
            保存对话历史
                     ↓
            返回 AI 回复
```

## 容错设计

- **降级策略**：LangChain Agent → OpenAI 直连 → 预设回复库，任一层失败自动落到下一层
- **视觉缺失**：`ZHIPU_API_KEY` 为空时图片被丢弃并打印告警，对话不中断
- **图像生成**：`ZHIPU_IMAGE_MODEL` 置空或远程调用失败时自动生成本地 SVG 头像
- **RAG**：Chroma 不可用时退化为内存检索；Embedding 使用本地哈希向量（未接入远程 Embedding API）

## 注意事项

1. **API 密钥安全**: 密钥只写入 `.env`（gitignore 已忽略），不要提交到代码仓库或写入文档
2. **Token 用量**: 智谱按 token 计费（文本/视觉）；CogView 按生成张数计费，具体单价见智谱控制台
3. **服务依赖**: Java 后端依赖 Python AI 服务，需要按顺序启动
4. **网络连接**: 确保可以访问 `open.bigmodel.cn`
