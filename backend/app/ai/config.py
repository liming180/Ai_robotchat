"""
智谱 AI API 配置模块
独立存放所有 API 配置，避免硬编码
"""
import os
from dataclasses import dataclass


@dataclass
class ZhipuAIConfig:
    """智谱 AI 配置类"""
    API_KEY: str = ""  # 从环境变量 ZHIPU_API_KEY 读取，禁止硬编码
    BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    MODEL: str = "glm-4.5-air"
    VISION_MODEL: str = "glm-4v-flash"
    IMAGE_MODEL: str = "cogview-3"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1024
    TOP_P: float = 0.9
    
    def __post_init__(self):
        """兜底：未显式传值时，从环境变量补齐关键配置。

        这样 ZhipuAIConfig() 与 ZhipuAIConfig.from_env() 行为一致，
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
        if _os.getenv("ZHIPU_BASE_URL"):
            self.BASE_URL = _os.getenv("ZHIPU_BASE_URL").strip()
        if _os.getenv("ZHIPU_MODEL"):
            self.MODEL = _os.getenv("ZHIPU_MODEL").strip()
        if _os.getenv("ZHIPU_VISION_MODEL"):
            self.VISION_MODEL = _os.getenv("ZHIPU_VISION_MODEL").strip()
        if _os.getenv("ZHIPU_IMAGE_MODEL"):
            self.IMAGE_MODEL = _os.getenv("ZHIPU_IMAGE_MODEL").strip()

    @classmethod
    def from_env(cls):
        """从环境变量加载配置（env-first）"""
        api_key = os.getenv("ZHIPU_API_KEY", "").strip()
        base_url = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        model = os.getenv("ZHIPU_MODEL", "glm-4.5-air")
        vision_model = os.getenv("ZHIPU_VISION_MODEL", "glm-4v-flash")
        image_model = os.getenv("ZHIPU_IMAGE_MODEL", "cogview-3")
        temperature = float(os.getenv("ZHIPU_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("ZHIPU_MAX_TOKENS", "1024"))
        top_p = float(os.getenv("ZHIPU_TOP_P", "0.9"))
        
        return cls(
            API_KEY=api_key,
            BASE_URL=base_url,
            MODEL=model,
            VISION_MODEL=vision_model,
            IMAGE_MODEL=image_model,
            TEMPERATURE=temperature,
            MAX_TOKENS=max_tokens,
            TOP_P=top_p
        )
    
    def is_valid(self):
        """检查配置是否有效"""
        return bool(self.API_KEY and self.API_KEY.strip())
    
    def __str__(self):
        """安全打印配置（隐藏密钥）"""
        masked_key = ""
        if self.API_KEY:
            if len(self.API_KEY) > 12:
                masked_key = self.API_KEY[:8] + "..." + self.API_KEY[-4:]
            else:
                masked_key = "****"
        
        return "ZhipuAIConfig(\n  BASE_URL=" + self.BASE_URL + ",\n  MODEL=" + self.MODEL + ",\n  VISION_MODEL=" + self.VISION_MODEL + ",\n  IMAGE_MODEL=" + self.IMAGE_MODEL + ",\n  TEMPERATURE=" + str(self.TEMPERATURE) + ",\n  MAX_TOKENS=" + str(self.MAX_TOKENS) + ",\n  API_KEY=" + masked_key + "\n)"


_zhipu_config = None


def get_zhipu_config():
    """获取智谱 AI 配置（单例模式）"""
    global _zhipu_config
    if _zhipu_config is None:
        _zhipu_config = ZhipuAIConfig.from_env()
    return _zhipu_config


def reload_config():
    """重新加载配置"""
    global _zhipu_config
    _zhipu_config = None
    return get_zhipu_config()
