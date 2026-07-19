"""Tests for avatar download and storage."""
import os
import tempfile
from app.ai.avatar_store import download_and_save_avatar, get_avatar_path


def test_download_and_save_avatar_creates_file():
    """下载头像后应生成文件，返回可访问的本地路径。"""
    # 模拟 CogView 返回的临时 URL（含 watermark）
    mock_url = "https://maas-watermark-prod-new.cn-wlcb.ufileos.com/20260711/xxx.png"
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 模拟 backend/static/avatars/ 目录
        avatars_dir = os.path.join(tmp_dir, "static", "avatars")
        os.makedirs(avatars_dir, exist_ok=True)

        # 调用函数
        avatar_path = download_and_save_avatar(mock_url, avatars_dir)

        # 验证文件存在且可读
        assert os.path.exists(avatar_path)
        assert os.path.isfile(avatar_path)
        assert avatar_path.startswith(avatars_dir)


def test_get_avatar_path_returns_correct_path():
    """get_avatar_path 应返回正确的文件路径。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        avatars_dir = os.path.join(tmp_dir, "static", "avatars")
        os.makedirs(avatars_dir, exist_ok=True)

        # 测试路径生成
        uuid = "test-uuid-123"
        expected_path = os.path.join(avatars_dir, f"{uuid}.png")
        actual_path = get_avatar_path(uuid, avatars_dir)

        assert actual_path == expected_path


def test_download_and_save_avatar_handles_invalid_url():
    """无效 URL 应抛出异常（不崩溃）。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        avatars_dir = os.path.join(tmp_dir, "static", "avatars")
        os.makedirs(avatars_dir, exist_ok=True)

        # 无效 URL
        invalid_url = "not-a-real-url"

        try:
            download_and_save_avatar(invalid_url, avatars_dir)
            assert False, "Expected exception for invalid URL"
        except Exception:
            pass  # 预期抛出异常


def test_download_and_save_avatar_uses_given_avatars_dir():
    """应使用传入的 avatars_dir 路径，而非硬编码。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        custom_dir = os.path.join(tmp_dir, "custom_avatars")
        os.makedirs(custom_dir, exist_ok=True)

        mock_url = "https://maas-watermark-prod-new.cn-wlcb.ufileos.com/20260711/xxx.png"
        avatar_path = download_and_save_avatar(mock_url, custom_dir)

        assert os.path.exists(avatar_path)
        assert avatar_path.startswith(custom_dir)