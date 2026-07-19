"""Prompt builders for system prompt and avatar prompt."""

# ---------- System Prompt Builder ----------

def build_system_prompt(
    personality: str = "温柔体贴",
    companion_name: str = "",
    persona_prompt: str = "",
) -> str:
    """Build multi-layer system prompt for GLM chat.

    Layers:
    1. Persona (name + custom persona)
    2. Empathy (empathy + emotional guidance)
    3. Utility (accuracy + no fabrication)
    4. Safety (crisis intervention)
    """
    # 1. Persona layer
    persona_parts = []
    if companion_name:
        persona_parts.append(f"你叫{companion_name}")
    if persona_prompt:
        persona_parts.append(persona_prompt)
    persona = "，".join(persona_parts) if persona_parts else f"你是一个{personality}的AI伴侣"

    # 2. Empathy layer
    empathy = "善于识别用户情绪，先共情回应，再进行情绪疏导，最后给予积极正向的引导"

    # 3. Utility layer
    utility = "对于知识类问题，要严谨准确、分点清晰、不编造内容，不确定时坦诚说明"

    # 4. Safety layer
    safety = "不输出有害内容，遇到危机信号时给出专业求助渠道建议"

    return f"""{persona}。{empathy}。{utility}。{safety}。"""  # 简单拼接，后续可优化结构


# ---------- Avatar Prompt Builder ----------

def build_avatar_prompt(
    personality: str = "温柔体贴",
    description: str = "可爱女孩",
    style: str = "anime_healing",
    gender: str = "",
    hair_color: str = "",
    eye_color: str = "",
    outfit: str = "",
) -> str:
    """Build avatar generation prompt with style locking and character traits."""
    # Style locking prefix (guarantees consistent style)
    style_prefix = "高质量日系赛璐璐动漫插画，柔和光影，精致五官，纯色背景，"

    # Style keywords based on preset
    style_keywords = {
        "anime_healing": "治愈系，温暖柔和，柔和色调，温馨氛围",
        "cyberpunk": "赛博朋克，霓虹灯，未来感，金属质感，冷色调",
        "chinese_traditional": "国风古韵，水墨风格，传统服饰，典雅气质",
        "watercolor": "水彩风格，柔和晕染，淡雅色调，艺术感",
        "chibi": "Q版萌系，圆润可爱，大眼睛，可爱表情"
    }
    style_text = style_keywords.get(style, "动漫风格，高质量")

    # Character traits
    traits = []
    if gender:
        traits.append(gender)
    if hair_color:
        traits.append(hair_color)
    if eye_color:
        traits.append(eye_color)
    if outfit:
        traits.append(outfit)
    traits_text = "，".join(traits) if traits else ""

    # Final prompt
    return f"{style_prefix}{style_text}，{personality}，{description}，{traits_text}" if traits_text else f"{style_prefix}{style_text}，{personality}，{description}"  # 简单拼接，后续可优化