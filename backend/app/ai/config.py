"""
LLM API 配置模块
单平台架构：智谱 GLM（文本 glm-4.5-air + 视觉 glm-4v-flash，共用同一 key）
独立存放所有 API 配置，避免硬编码；所有配置 env 优先。

字段名沿用 API_KEY / BASE_URL / MODEL / VISION_* 不改，只把读取来源
换成 ZHIPU_* 环境变量，避免改动所有调用方（langchain_client.py 等）。
"""
import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM 配置类（文本 / 视觉 / 图像生成）"""

    # ── 文本链路（智谱 GLM：对话 / suggestions / RAG / tool calling） ──
    API_KEY: str = ""  # 从环境变量 ZHIPU_API_KEY 读取，禁止硬编码
    BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    MODEL: str = "glm-4.5-air"

    # ── 视觉链路（智谱 GLM：图片理解） ──
    VISION_API_KEY: str = ""  # 默认与文本链路同 key，ZHIPU_VISION_* 可单独覆盖
    VISION_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    VISION_MODEL: str = "glm-4v-flash"

    # ── 图像生成（空字符串 = 走本地 SVG 头像降级） ──
    IMAGE_MODEL: str = ""

    # ── 采样参数（两条链路共用） ──
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1024
    TOP_P: float = 0.9

    def __post_init__(self):
        """兜底：未显式传值时，从环境变量补齐关键配置。

        这样 LLMConfig() 与 LLMConfig.from_env() 行为一致，
        避免调用方忘记传值导致 API_KEY 为空。
        """
        import os as _os
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass

        if not self.API_KEY or not str(self.API_KEY).strip():
            self.API_KEY = _os.getenv("ZHIPU_API_KEY", "").strip()
        # GLM 的文本与视觉共用同一个 key；未单独配置视觉 key 时沿用它
        if not self.VISION_API_KEY or not str(self.VISION_API_KEY).strip():
            self.VISION_API_KEY = _os.getenv("ZHIPU_VISION_API_KEY", "").strip() or self.API_KEY
        if _os.getenv("ZHIPU_BASE_URL"):
            self.BASE_URL = _os.getenv("ZHIPU_BASE_URL").strip()
            self.VISION_BASE_URL = self.BASE_URL
        if _os.getenv("ZHIPU_MODEL"):
            self.MODEL = _os.getenv("ZHIPU_MODEL").strip()
        if _os.getenv("ZHIPU_VISION_BASE_URL"):
            self.VISION_BASE_URL = _os.getenv("ZHIPU_VISION_BASE_URL").strip()
        if _os.getenv("ZHIPU_VISION_MODEL"):
            self.VISION_MODEL = _os.getenv("ZHIPU_VISION_MODEL").strip()
        if "ZHIPU_IMAGE_MODEL" in _os.environ:
            self.IMAGE_MODEL = _os.getenv("ZHIPU_IMAGE_MODEL", "").strip()
        if _os.getenv("LLM_TEMPERATURE"):
            self.TEMPERATURE = float(_os.getenv("LLM_TEMPERATURE"))
        if _os.getenv("LLM_MAX_TOKENS"):
            self.MAX_TOKENS = int(_os.getenv("LLM_MAX_TOKENS"))
        if _os.getenv("LLM_TOP_P"):
            self.TOP_P = float(_os.getenv("LLM_TOP_P"))

    @classmethod
    def from_env(cls):
        """从环境变量加载配置（env-first）"""
        api_key = os.getenv("ZHIPU_API_KEY", "").strip()
        base_url = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").strip()
        return cls(
            API_KEY=api_key,
            BASE_URL=base_url,
            MODEL=os.getenv("ZHIPU_MODEL", "glm-4.5-air").strip(),
            # GLM 文本与视觉共用一个 key；ZHIPU_VISION_API_KEY 仅用于单独覆盖
            VISION_API_KEY=os.getenv("ZHIPU_VISION_API_KEY", "").strip() or api_key,
            VISION_BASE_URL=os.getenv("ZHIPU_VISION_BASE_URL", base_url).strip(),
            VISION_MODEL=os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash").strip(),
            IMAGE_MODEL=os.getenv("ZHIPU_IMAGE_MODEL", "").strip(),
            TEMPERATURE=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            MAX_TOKENS=int(os.getenv("LLM_MAX_TOKENS", "1024")),
            TOP_P=float(os.getenv("LLM_TOP_P", "0.9")),
        )

    def is_valid(self):
        """检查文本链路配置是否有效"""
        return bool(self.API_KEY and self.API_KEY.strip())

    def is_vision_valid(self):
        """检查视觉链路配置是否有效"""
        return bool(self.VISION_API_KEY and self.VISION_API_KEY.strip())

    @staticmethod
    def _mask(key: str) -> str:
        if not key:
            return ""
        if len(key) > 12:
            return key[:8] + "..." + key[-4:]
        return "****"

    def __str__(self):
        """安全打印配置（隐藏密钥）"""
        return (
            "LLMConfig(\n"
            "  文本链路 BASE_URL=" + self.BASE_URL + ", MODEL=" + self.MODEL + "\n"
            "  视觉链路 BASE_URL=" + self.VISION_BASE_URL + ", MODEL=" + self.VISION_MODEL + "\n"
            "  IMAGE_MODEL=" + (self.IMAGE_MODEL or "(空，本地 SVG 降级)") + "\n"
            "  TEMPERATURE=" + str(self.TEMPERATURE)
            + ", MAX_TOKENS=" + str(self.MAX_TOKENS)
            + ", TOP_P=" + str(self.TOP_P) + "\n"
            "  MODEL_API_KEY=" + self._mask(self.API_KEY) + "\n"
            "  VISION_API_KEY=" + self._mask(self.VISION_API_KEY) + "\n"
            ")"
        )


_llm_config = None


def get_llm_config():
    """获取 LLM 配置（单例模式）"""
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig.from_env()
    return _llm_config


def reload_config():
    """重新加载配置"""
    global _llm_config
    _llm_config = None
    return get_llm_config()
