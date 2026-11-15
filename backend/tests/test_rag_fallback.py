"""Tests for search_knowledge RAG fallback logic.

验证 8002 RAG 服务与本地 RAGStore 的回落行为：
- 8002 正常返回 chunks → 用远程结果
- 8002 正常返回空 chunks → 不回落，直接返回空提示
- 8002 超时 → 回落本地
- 8002 连接异常 → 回落本地
- 8002 返回 5xx → 回落本地
"""
import pytest
from unittest.mock import patch, MagicMock
import requests

from app.ai.langchain_client import _search_knowledge_remote


class MockConfig:
    RAG_SERVICE_URL = "http://localhost:8002"
    RAG_TIMEOUT = 3


CONFIG = MockConfig()


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = str(json_data or "")
    return resp


# ── 8002 正常返回 chunks ──

def test_remote_returns_chunks():
    """8002 返回有内容的 chunks → 直接返回拼接文本"""
    resp = _mock_response(200, {
        "success": True,
        "data": {
            "chunks": [
                {"content": " 用户喜欢猫 ", "score": 0.9},
                {"content": "用户住在北京", "score": 0.8},
            ]
        }
    })
    with patch("requests.post", return_value=resp):
        result = _search_knowledge_remote("comp-1", "宠物", CONFIG)
    assert result == "用户喜欢猫\n用户住在北京"


# ── 8002 正常返回空 chunks → 不回落 ──

def test_remote_returns_empty_chunks():
    """8002 返回空 chunks（正常业务结果）→ 返回提示语，不抛异常"""
    resp = _mock_response(200, {
        "success": True,
        "data": {"chunks": []}
    })
    with patch("requests.post", return_value=resp):
        result = _search_knowledge_remote("comp-1", "不存在的知识", CONFIG)
    assert result == "知识库中没有找到相关内容。"


# ── 8002 超时 → 抛异常（调用方回落） ──

def test_remote_timeout_raises():
    """8002 超时 → 抛 requests.Timeout，由调用方回落本地"""
    with patch("requests.post", side_effect=requests.Timeout("timeout")):
        with pytest.raises(requests.Timeout):
            _search_knowledge_remote("comp-1", "查询", CONFIG)


# ── 8002 连接异常 → 抛异常（调用方回落） ──

def test_remote_connection_error_raises():
    """8002 连接拒绝 → 抛 requests.ConnectionError，由调用方回落本地"""
    with patch("requests.post", side_effect=requests.ConnectionError("refused")):
        with pytest.raises(requests.ConnectionError):
            _search_knowledge_remote("comp-1", "查询", CONFIG)


# ── 8002 返回 5xx → 抛异常（调用方回落） ──

def test_remote_5xx_raises():
    """8002 返回 500 → 抛 RuntimeError，由调用方回落本地"""
    resp = _mock_response(500, {"detail": "Internal Server Error"})
    with patch("requests.post", return_value=resp):
        with pytest.raises(RuntimeError, match="500"):
            _search_knowledge_remote("comp-1", "查询", CONFIG)


# ── 8002 返回 4xx → 返回 None（不抛异常，但也不回落） ──

def test_remote_4xx_returns_none():
    """8002 返回 400 → 返回 None（不抛异常，调用方视为无结果）"""
    resp = _mock_response(400, {"detail": "Bad Request"})
    with patch("requests.post", return_value=resp):
        result = _search_knowledge_remote("comp-1", "查询", CONFIG)
    assert result is None
