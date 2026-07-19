"""Tests for GLM client (httpx direct calls)."""
import os
from unittest.mock import Mock, patch
from app.ai.glm_client import GLMClient, GLMClientError


def test_glm_client_init_with_valid_key():
    """初始化应成功（用 .env 里的 key）。"""
    client = GLMClient()
    assert client.api_key is not None
    assert client.base_url == "https://open.bigmodel.cn/api/paas/v4"


def test_glm_client_chat_with_system_prompt():
    """带系统提示词的聊天应返回内容。"""
    client = GLMClient()

    # 模拟成功响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "你好！很高兴见到你。"}}]
    }

    with patch("httpx.Client.post", return_value=mock_response):
        response = client.chat(
            model="glm-4-flash",
            messages=[{"role": "user", "content": "你好"}],
            system_prompt="你是一个温柔体贴的AI伴侣",
        )

    assert "content" in response
    assert isinstance(response["content"], str)
    assert response["content"] == "你好！很高兴见到你。"


def test_glm_client_chat_stream():
    """流式聊天应返回生成器，逐 token 生成。"""
    client = GLMClient()

    # 模拟流式响应（多个 token）
    mock_stream = Mock()
    mock_stream.__iter__.return_value = iter([
        '{"choices":[{"delta":{"content":"你"}}',
        '{"choices":[{"delta":{"content":"好"}}',
        '{"choices":[{"delta":{"content":"！"}}',
        '{"choices":[{"delta":{"content":"很高兴"}}',
        '{"choices":[{"delta":{"content":"见到"}}',
        '{"choices":[{"delta":{"content":"你"}}',
        '{"choices":[{"delta":{"content":"。"}}',
        '{"choices":[{"delta":{}}]'  # 结束
    ])

    with patch("httpx.Client.post", return_value=mock_stream):
        stream = client.chat_stream(
            model="glm-4-flash",
            messages=[{"role": "user", "content": "你好"}],
            system_prompt="你是一个温柔体贴的AI伴侣",
        )

        # 检查是否是生成器
        assert hasattr(stream, "__iter__") or hasattr(stream, "__next__")

        # 消耗并拼接 token
        result = "".join(stream)
        assert result == "你好！很高兴见到你。"


def test_glm_client_generate_image():
    """文生图应返回图片 URL。"""
    client = GLMClient()

    # 模拟成功响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"url": "https://example.com/avatar.png"}]
    }

    with patch("httpx.Client.post", return_value=mock_response):
        response = client.generate_image(
            model="cogview-3",
            prompt="可爱的动漫女孩，温柔体贴，高清",
        )

    assert "url" in response
    assert isinstance(response["url"], str)
    assert response["url"] == "https://example.com/avatar.png"


def test_glm_client_handles_api_error():
    """API 错误应抛出 GLMClientError。"""
    client = GLMClient()

    # 模拟错误响应
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Invalid prompt"}

    with patch("httpx.Client.post", return_value=mock_response):
        try:
            client.chat(model="glm-4-flash", messages=[{"role": "user", "content": ""}])
            assert False, "Expected GLMClientError"
        except GLMClientError as e:
            assert "API error" in str(e) or "status" in str(e)