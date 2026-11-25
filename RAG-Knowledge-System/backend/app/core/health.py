"""系统依赖探活（2026-11-25 可用性收口）。

`/health` 要回答的是「这个进程还能不能干活」，而不是「进程还在不在」。
此前只检查 import 期的 `engine is not None`，Milvus 停机时仍返回 200，
真实故障被掩盖成 25s 检索超时（docs/04 P2-5 动作 3 遗留②）。

三条口径：
1. **独立短超时**：不复用检索链路（5000 侧 RAG_TIMEOUT=3s、前端 90s），
   pymilvus 建连实测停机时 1.5~2.1s（timeout 生效但有约 2s 下限），默认 2.0s。
2. **只用 get_server_version()**：`milvus_rag` 有权限、健康时 1~46ms。
   禁用 `list_collections()`——Milvus 2.6.0 对非 root 用户报
   `etcdserver: invalid auth token`（服务端缺陷，8002 从不调它）。
3. **同步阻塞**：pymilvus 不是异步库，调用方（`/health`）必须是普通 `def`，
   由 FastAPI 线程池执行，否则会堵住整个事件循环。
"""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict

from app.core.config import settings

logger = logging.getLogger(__name__)

# 探活结果缓存：1s 内复用，避免并发 /health（start-all 每秒轮询）各自建一次 gRPC 连接。
# 取舍：故障后最多 1s 才发现，仍满足「立即非 200」；换来的是不会把 Milvus 打爆。
CACHE_TTL_SECONDS = 1.0

_lock = threading.Lock()
_cache: Dict[str, Any] = {"ts": 0.0, "result": None}
_last_logged_status: str | None = None

# 连接失败时 pymilvus 会打 ERROR + 完整 traceback（[ERROR][_log_rpc_error]）。
# 探活是可预期的高频失败，不能让它淹没 8002 日志；只在探活窗口内临时调高这些 logger。
_PYMILVUS_LOGGERS = (
    "pymilvus",
    "pymilvus.client",
    "pymilvus.client.grpc_handler",
    "pymilvus.decorators",
)


@contextmanager
def _muted_pymilvus_logs():
    """探活期间屏蔽 pymilvus 的错误日志，结束后恢复原级别。"""
    saved = [(logging.getLogger(name), logging.getLogger(name).level) for name in _PYMILVUS_LOGGERS]
    for lg, _ in saved:
        lg.setLevel(logging.CRITICAL)
    try:
        yield
    finally:
        for lg, level in saved:
            lg.setLevel(level)


def _disabled(reason: str) -> Dict[str, Any]:
    return {"status": "disabled", "latencyMs": 0, "version": None, "error": reason}


def probe_milvus() -> Dict[str, Any]:
    """探测 Milvus 是否可用。

    Returns:
        {
          "status": "connected" | "unavailable" | "disabled",
          "latencyMs": int,
          "version": str | None,   # 连接成功时的服务端版本，如 "2.6.0"
          "error": str | None,     # 失败原因（截断 200 字），不打印口令
        }
    """
    global _last_logged_status

    if settings.vector_store_backend != "milvus":
        return _disabled(f"vector_store_backend={settings.vector_store_backend}")
    if not settings.milvus_health_enabled:
        return _disabled("MILVUS_HEALTH_ENABLED=false")

    with _lock:
        cached = _cache["result"]
        if cached is not None and (time.monotonic() - _cache["ts"]) < CACHE_TTL_SECONDS:
            return dict(cached)

        started = time.monotonic()
        status, version, error = "unavailable", None, None
        client = None
        try:
            with _muted_pymilvus_logs():
                from pymilvus import MilvusClient  # 延迟导入：chroma 回退时不必加载

                client = MilvusClient(
                    uri=f"http://{settings.milvus_host}:{settings.milvus_port}",
                    user=settings.milvus_user or "",
                    password=settings.milvus_password or "",
                    timeout=settings.milvus_health_timeout,
                )
                version = client.get_server_version()
            status = "connected"
        except Exception as exc:  # noqa: BLE001 - 探活必须吃掉所有异常
            error = f"{type(exc).__name__}: {str(exc)[:200]}"
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:  # noqa: BLE001
                    pass

        result = {
            "status": status,
            "latencyMs": int((time.monotonic() - started) * 1000),
            "version": version,
            "error": error,
        }
        _cache["ts"] = time.monotonic()
        _cache["result"] = result

        # 只在状态翻转时写一行日志，避免每 1s 刷屏
        if status != _last_logged_status:
            if status == "connected":
                logger.warning("[health] Milvus 恢复: version=%s latency=%dms", version, result["latencyMs"])
            else:
                logger.warning("[health] Milvus 不可用: %s", error)
            _last_logged_status = status

        return dict(result)


def reset_cache() -> None:
    """清空探活缓存（测试用）。"""
    global _last_logged_status
    with _lock:
        _cache["ts"] = 0.0
        _cache["result"] = None
        _last_logged_status = None
