"""锁定 `/health` 的 Milvus 探活语义（2026-11-25 可用性收口）。

验收口径：
- Milvus 可用 → 200，data.milvus=connected；
- Milvus 不可用 → **503**（不再「进程活着就 200」），body 仍是统一 fail 结构；
- 向量库后端是 chroma 或显式关闭探活 → 200，data.milvus=disabled；
- `/health` 必须是普通 def（pymilvus 同步阻塞，async 会堵事件循环）。

运行：
    cd RAG-Knowledge-System/backend
    python -m pytest tests/test_health_milvus.py -q
"""

import inspect
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import main  # noqa: E402
from app.core import health as health_module  # noqa: E402

# 不进入 with：避免触发 lifespan（JWT 自检、Milvus 初始化），只测路由函数本身
client = TestClient(main.app)


def _patch_probe(monkeypatch, result):
    monkeypatch.setattr(main, "probe_milvus", lambda: result)


def test_health_is_sync_callable():
    """pymilvus 是同步阻塞调用，/health 必须是普通 def（FastAPI 走线程池）。"""
    assert inspect.iscoroutinefunction(main.health) is False


def test_health_ok_when_milvus_connected(monkeypatch):
    _patch_probe(monkeypatch, {"status": "connected", "latencyMs": 12, "version": "2.6.0", "error": None})

    resp = client.get("/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["milvus"] == "connected"
    assert body["data"]["milvusVersion"] == "2.6.0"
    assert body["data"]["vectorStore"] == "milvus"
    # 原有字段保持不变（前端 HealthInfo 依赖）
    assert body["data"]["service"] == "RAG_Knowledge_System"


def test_health_503_when_milvus_unavailable(monkeypatch):
    _patch_probe(
        monkeypatch,
        {"status": "unavailable", "latencyMs": 2000, "version": None, "error": "MilvusException: connection refused"},
    )

    resp = client.get("/health")

    assert resp.status_code == 503
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "MILVUS_UNAVAILABLE"
    assert body["data"]["milvus"] == "unavailable"
    assert "MilvusException" in body["message"]


def test_health_200_when_probe_disabled(monkeypatch):
    _patch_probe(monkeypatch, {"status": "disabled", "latencyMs": 0, "version": None, "error": "chroma"})

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json()["data"]["milvus"] == "disabled"


def test_probe_disabled_for_chroma_backend(monkeypatch):
    """chroma 回退时不得因 Milvus 不通而把 /health 拉成 503。"""
    health_module.reset_cache()
    monkeypatch.setattr(health_module.settings, "vector_store_backend", "chroma")

    result = health_module.probe_milvus()

    assert result["status"] == "disabled"
    assert result["latencyMs"] == 0


def test_probe_disabled_by_switch(monkeypatch):
    health_module.reset_cache()
    monkeypatch.setattr(health_module.settings, "vector_store_backend", "milvus")
    monkeypatch.setattr(health_module.settings, "milvus_health_enabled", False)

    result = health_module.probe_milvus()

    assert result["status"] == "disabled"
    assert "MILVUS_HEALTH_ENABLED" in result["error"]


def test_probe_failure_is_swallowed(monkeypatch):
    """探活失败必须返回 unavailable，绝不能把异常抛给 /health。"""
    health_module.reset_cache()
    monkeypatch.setattr(health_module.settings, "vector_store_backend", "milvus")
    monkeypatch.setattr(health_module.settings, "milvus_health_enabled", True)

    class Boom:
        def __init__(self, **kwargs):
            raise RuntimeError("cannot connect")

    monkeypatch.setitem(sys.modules, "pymilvus", type("M", (), {"MilvusClient": Boom}))

    result = health_module.probe_milvus()

    assert result["status"] == "unavailable"
    assert "cannot connect" in result["error"]
