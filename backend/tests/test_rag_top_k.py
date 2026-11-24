"""LLMConfig.RAG_TOP_K 环境变量解析与夹取测试。"""
import pytest

from app.ai.config import LLMConfig


@pytest.mark.parametrize("raw,expected", [
    ("8", 8),
    ("1", 1),
    ("20", 20),
    ("25", 20),      # 上界
    ("0", 1),        # 下界
    ("-5", 1),       # 负数
    ("abc", 8),      # 非数字回落默认
    (" 8 ", 8),      # 两侧空白
])
def test_rag_top_k_env_is_clamped(monkeypatch, raw, expected):
    monkeypatch.setenv("RAG_TOP_K", raw)
    assert LLMConfig().RAG_TOP_K == expected


def test_rag_top_k_default_when_env_absent(monkeypatch):
    monkeypatch.delenv("RAG_TOP_K", raising=False)
    assert LLMConfig().RAG_TOP_K == 8
