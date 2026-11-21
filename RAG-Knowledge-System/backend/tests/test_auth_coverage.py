"""鉴权覆盖率断言（2026-11-21 鉴权强制化第二批）。

作用：防止将来新增路由忘记挂鉴权依赖。直接解析 ``main.py`` 的真实路由表，
而不是扫描源码正则——这样 FastAPI 的挂载结果就是唯一事实来源。

运行：
    cd RAG-Knowledge-System/backend
    python -m pytest tests/test_auth_coverage.py -q
"""

import sys
from pathlib import Path

import pytest
from fastapi.routing import APIRoute

# 允许 `pytest tests/...` 直接在 backend 目录下运行
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# 白名单：明确不需要鉴权的端点（路径, 方法）
WHITELIST = {
    ("/health", "GET"),
    ("/", "GET"),
    ("/docs", "GET"),
    ("/openapi.json", "GET"),
    ("/redoc", "GET"),
    ("/api/v1/auth/login", "POST"),
}

# 白名单路径的「后缀」形式，用于匹配未带 prefix 的展开结果
WHITELIST_SUFFIX = {"/api/v1/auth/login"}

# retrieve 用服务间共享密钥，其余管理接口用 JWT。
# 注意：FastAPI 0.162 的 _IncludedRouter 包装对象不携带 prefix，
# 展开后的 route.path 是相对路径（/retrieve），故按后缀匹配。
SERVICE_TOKEN_PATHS = {"/retrieve"}


def _iter_api_routes():
    """递归展开真实路由。

    FastAPI 0.162 起 ``include_router`` 产生的是 ``_IncludedRouter`` 包装对象，
    ``app.routes`` 里不再是扁平的 ``APIRoute``；必须经 ``original_router``
    再递归，才能拿到带 prefix 的最终路径。
    """
    from main import app

    def walk(routes):
        for route in routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    if method in ("HEAD", "OPTIONS"):
                        continue
                    yield route, method.upper()
                continue
            original = getattr(route, "original_router", None)
            if original is not None and hasattr(original, "routes"):
                yield from walk(original.routes)

    yield from walk(app.routes)


def _dependency_names(route: APIRoute) -> set[str]:
    """收集该路由所有依赖的函数名（含嵌套依赖）。"""
    names = set()

    def walk(dependant):
        for dep in dependant.dependencies:
            if dep.call is not None:
                names.add(dep.call.__name__)
            walk(dep)

    walk(route.dependant)
    return names


def _is_whitelisted(path: str, method: str) -> bool:
    if (path, method) in WHITELIST:
        return True
    return any(path.endswith(suffix) for suffix in WHITELIST_SUFFIX) and method == "POST"


def test_all_routes_have_auth():
    """白名单之外，每条路由都必须挂鉴权依赖。"""
    missing = []
    for route, method in _iter_api_routes():
        if _is_whitelisted(route.path, method):
            continue
        deps = _dependency_names(route)
        has_jwt = "verify_jwt" in deps
        has_service = "verify_service_token" in deps
        if not (has_jwt or has_service):
            missing.append(f"{method} {route.path}")

    assert not missing, (
        "以下路由缺少鉴权依赖，请在装饰器加 dependencies=[Depends(verify_jwt)]：\n  "
        + "\n  ".join(sorted(missing))
    )


def test_retrieve_uses_service_token():
    """/retrieve 必须用服务间 token（5000 调用），不能要求 JWT。"""
    for route, method in _iter_api_routes():
        if any(route.path.endswith(p) for p in SERVICE_TOKEN_PATHS):
            deps = _dependency_names(route)
            assert "verify_service_token" in deps, f"{method} {route.path} 缺少 verify_service_token"
            assert "verify_jwt" not in deps, f"{method} {route.path} 不应要求 JWT（5000 无用户令牌）"
            return
    pytest.fail("未找到 /retrieve 路由")


def test_whitelist_routes_exist():
    """白名单里的路径必须真实存在，避免路径改名后白名单变成隐形豁免。"""
    actual = {(route.path, method) for route, method in _iter_api_routes()}
    actual_paths = {path for path, _ in actual}
    for path, method in WHITELIST:
        if path in ("/docs", "/openapi.json", "/redoc"):
            continue  # FastAPI 内置文档路由，不挂在 APIRoute 列表里
        found = (path, method) in actual or any(p.endswith(path) for p in actual_paths)
        assert found, f"白名单路径不存在，请同步更新：{method} {path}"
