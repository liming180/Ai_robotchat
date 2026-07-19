# main.py 重写：SSE 流式聊天 + 头像生成 + 静态服务

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 `main.py` 重写为使用 `app.ai.glm_client`（httpx 直调）的 SSE 流式聊天 + 头像生成 + 静态服务，替代旧版 `zhipuai` SDK 实现。

**Architecture:** 前端直连 Python 服务（3000→5000），Python 用 httpx 直调智谱 API。SSE 流式聊天（`/api/v1/ai/chat/stream`）替代旧版 `/api/v1/ai/chat`，头像生成（`/api/v1/ai/generate-avatar`）用 `app.ai.avatar_store` 落盘，挂载 `/static` 目录返回稳定 URL。

**Tech Stack:** FastAPI, httpx, SSE (text/event-stream), Python 文件操作

---

### Task 1: 添加 SSE 流式聊天端点

**Files:**
- Modify: `backend/main.py:247-269` (替换旧版 chat 端点)
- Test: `tests/test_main.py` (新增流式聊天测试)

**Step 1: 写失败测试（测试 SSE 流式聊天端点）**
```python
def test_chat_stream_endpoint():
    """测试 SSE 流式聊天端点返回生成器。"""
    response = client.post(
        "/api/v1/ai/chat/stream",
        json={
            "systemPrompt": "你是一个温柔体贴的AI伴侣",
            "messages": [],
            "userMessage": "你好"
        },
        headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    # 检查是否是 SSE 流
    assert "data: " in response.text[:100]
```

**Step 2: 运行测试确认失败**
```bash
python -m pytest tests/test_main.py::test_chat_stream_endpoint -v
```
Expected: FAIL (端点不存在)

**Step 3: 实现最小代码（添加 SSE 流式聊天端点）**
```python
@app.post("/api/v1/ai/chat/stream", tags=["AI"])
async def chat_stream(request: ChatRequest):
    """SSE 流式聊天端点。"""
    # 调用 glm_client 流式聊天
    client = GLMClient()
    stream = client.chat_stream(
        model=ZHIPU_MODEL,
        messages=request.messages,
        system_prompt=request.systemPrompt,
        user_message=request.userMessage
    )
    # 返回 SSE 流
    return StreamingResponse(
        stream,
        media_type="text/event-stream"
    )
```

**Step 4: 运行测试确认通过**
```bash
python -m pytest tests/test_main.py::test_chat_stream_endpoint -v
```
Expected: PASS

**Step 5: 提交**
```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: add SSE chat stream endpoint"
```

---

### Task 2: 重写头像生成端点（用 avatar_store 落盘）

**Files:**
- Modify: `backend/main.py:272-313` (替换旧版头像生成)
- Test: `tests/test_main.py` (新增头像生成测试)

**Step 1: 写失败测试（测试头像生成端点返回本地 URL）**
```python
def test_generate_avatar_endpoint():
    """测试头像生成端点返回本地文件 URL。"""
    response = client.post(
        "/api/v1/ai/generate-avatar",
        json={
            "personality": "温柔体贴",
            "description": "可爱女孩",
            "style": "anime_healing",
            "gender": "female"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "avatarUrl" in data
    # URL 应以 /static/ 开头（本地服务）
    assert data["avatarUrl"].startswith("/static/avatars/")
```

**Step 2: 运行测试确认失败**
```bash
python -m pytest tests/test_main.py::test_generate_avatar_endpoint -v
```
Expected: FAIL (端点逻辑不同)

**Step 3: 实现最小代码（头像生成 + 落盘）**
```python
@app.post("/api/v1/ai/generate-avatar", tags=["AI"])
async def generate_avatar(request: AvatarRequest):
    """头像生成端点（下载落盘返回本地 URL）。"""
    # 构建提示词
    prompt = build_avatar_prompt(
        personality=request.personality,
        description=request.description,
        style=request.style,
        gender=request.gender,
        hair_color=request.hair_color,
        eye_color=request.eye_color,
        outfit=request.outfit
    )
    
    # 调用 glm_client 生成图片
    client = GLMClient()
    image_data = client.generate_image(
        model=ZHIPU_IMAGE_MODEL,
        prompt=prompt
    )
    
    # 下载并保存到本地
    avatar_url = image_data["data"][0]["url"]
    avatar_path = download_and_save_avatar(
        avatar_url,
        "static/avatars"  # 相对路径，FastAPI 会挂载
    )
    
    if not avatar_path:
        raise HTTPException(status_code=500, detail="Failed to save avatar")
    
    # 返回本地 URL
    return APIResponse(
        success=True,
        message="Avatar generated and saved",
        data={
            "avatarUrl": f"/static/avatars/{os.path.basename(avatar_path)}"
        }
    )
```

**Step 4: 运行测试确认通过**
```bash
python -m pytest tests/test_main.py::test_generate_avatar_endpoint -v
```
Expected: PASS

**Step 5: 提交**
```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: rewrite avatar generation with local storage"
```

---

### Task 3: 挂载静态目录服务

**Files:**
- Modify: `backend/main.py:21-34` (添加静态目录挂载)

**Step 1: 写失败测试（测试静态文件可访问）**
```python
def test_static_avatar_access():
    """测试静态头像 URL 可访问。"""
    # 先调用生成头像端点获取 URL
    response = client.post(
        "/api/v1/ai/generate-avatar",
        json={"personality": "温柔体贴", "description": "可爱女孩"}
    )
    avatar_url = response.json()["data"]["avatarUrl"]
    
    # 提取文件名并访问静态文件
    filename = avatar_url.split("/")[-1]
    static_url = f"/static/avatars/{filename}"
    response = client.get(static_url)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
```

**Step 2: 运行测试确认失败**
```bash
python -m pytest tests/test_main.py::test_static_avatar_access -v
```
Expected: FAIL (静态目录未挂载)

**Step 3: 实现最小代码（挂载静态目录）**
```python
# 在 app 初始化后添加
app.mount(
    "/static",
    StaticFiles(directory="static", html=False),
    name="static"
)
```

**Step 4: 运行测试确认通过**
```bash
python -m pytest tests/test_main.py::test_static_avatar_access -v
```
Expected: PASS

**Step 5: 提交**
```bash
git add backend/main.py
git commit -m "feat: mount static directory for avatar serving"
```

---

### Task 4: 更新健康检查（包含新端点）

**Files:**
- Modify: `backend/main.py:221-234` (更新健康检查)

**Step 1: 写失败测试（测试健康检查包含新端点状态）**
```python
def test_health_check_includes_new_endpoints():
    """健康检查应包含新端点的可用性。"""
    response = client.get("/health")
    data = response.json()
    assert "chat_stream_available" in data
    assert "avatar_generation_available" in data
```

**Step 2: 运行测试确认失败**
```bash
python -m pytest tests/test_main.py::test_health_check_includes_new_endpoints -v
```
Expected: FAIL (字段不存在)

**Step 3: 实现最小代码（更新健康检查）**
```python
@app.get("/health", tags=["Health"])
async def health_check():
    return APIResponse(
        success=True,
        message="Service is healthy",
        data={
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "zhipu_available": True,  # httpx 可用
            "model": ZHIPU_MODEL,
            "image_model": ZHIPU_IMAGE_MODEL,
            "chat_stream_available": True,
            "avatar_generation_available": True
        },
        timestamp=datetime.utcnow().isoformat()
    )
```

**Step 4: 运行测试确认通过**
```bash
python -m pytest tests/test_main.py::test_health_check_includes_new_endpoints -v
```
Expected: PASS

**Step 5: 提交**
```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: update health check with new endpoint status"
```

---

### Task 5: 创建测试文件（tests/test_main.py）

**Files:**
- Create: `backend/tests/test_main.py`

**Step 1: 写失败测试（测试主应用路由）**
```python
def test_root_endpoint():
    """测试根路由返回欢迎信息。"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to AI Companion AI Service"
```

**Step 2: 运行测试确认失败**
```bash
python -m pytest tests/test_main.py::test_root_endpoint -v
```
Expected: FAIL (测试文件不存在)

**Step 3: 实现最小代码（创建测试文件）**
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """测试根路由返回欢迎信息。"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to AI Companion AI Service"

def test_chat_stream_endpoint():
    """测试 SSE 流式聊天端点返回生成器。"""
    response = client.post(
        "/api/v1/ai/chat/stream",
        json={
            "systemPrompt": "你是一个温柔体贴的AI伴侣",
            "messages": [],
            "userMessage": "你好"
        },
        headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    # 检查是否是 SSE 流
    assert "data: " in response.text[:100]

def test_generate_avatar_endpoint():
    """测试头像生成端点返回本地文件 URL。"""
    response = client.post(
        "/api/v1/ai/generate-avatar",
        json={
            "personality": "温柔体贴",
            "description": "可爱女孩",
            "style": "anime_healing",
            "gender": "female"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "avatarUrl" in data
    # URL 应以 /static/ 开头（本地服务）
    assert data["avatarUrl"].startswith("/static/avatars/")

def test_static_avatar_access():
    """测试静态头像 URL 可访问。"""
    # 先调用生成头像端点获取 URL
    response = client.post(
        "/api/v1/ai/generate-avatar",
        json={"personality": "温柔体贴", "description": "可爱女孩"}
    )
    avatar_url = response.json()["data"]["avatarUrl"]
    
    # 提取文件名并访问静态文件
    filename = avatar_url.split("/")[-1]
    static_url = f"/static/avatars/{filename}"
    response = client.get(static_url)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")

def test_health_check_includes_new_endpoints():
    """健康检查应包含新端点的可用性。"""
    response = client.get("/health")
    data = response.json()
    assert "chat_stream_available" in data
    assert "avatar_generation_available" in data
```

**Step 4: 运行测试确认通过**
```bash
python -m pytest tests/test_main.py -v
```
Expected: PASS

**Step 5: 提交**
```bash
git add backend/tests/test_main.py
git commit -m "feat: add main app tests"
```

---

Plan complete and saved to `docs/plans/2026-07-12-main-rewrite-plan.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?