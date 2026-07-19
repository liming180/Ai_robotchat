"""Avatar download and storage utilities."""
import os
import httpx
from typing import Optional


def get_avatar_path(uuid: str, avatars_dir: str) -> str:
    """Get the local file path for an avatar."""
    return os.path.join(avatars_dir, f"{uuid}.png")


def download_and_save_avatar(
    image_url: str, avatars_dir: str, timeout: int = 30
) -> Optional[str]:
    """Download avatar from URL and save to local storage.

    Args:
        image_url: URL of the avatar image (temporary, may have watermark)
        avatars_dir: Directory to save the avatar (e.g., "backend/static/avatars")
        timeout: HTTP request timeout in seconds

    Returns:
        Local file path if successful, None if failed
    """
    # Create directory if not exists
    os.makedirs(avatars_dir, exist_ok=True)

    # Generate unique filename
    avatar_path = get_avatar_path(str(os.urandom(16).hex()), avatars_dir)

    try:
        # Download the image
        response = httpx.get(image_url, timeout=timeout)
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes

        # Save to file
        with open(avatar_path, "wb") as f:
            f.write(response.content)

        return avatar_path
    except Exception as e:
        print(f"Failed to download avatar: {e}")
        # Clean up partially downloaded file if exists
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        return None