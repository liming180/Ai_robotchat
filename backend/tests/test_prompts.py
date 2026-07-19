"""Tests for prompt builders (system prompt + avatar prompt)."""
from app.ai.prompts import build_system_prompt, build_avatar_prompt


# ---------- build_system_prompt ----------

def test_system_prompt_contains_empathy_framework():
    """情感层：必须包含共情/情绪疏导/积极引导的引导词。"""
    prompt = build_system_prompt(personality="温柔体贴")
    assert "共情" in prompt or "情绪" in prompt
    # 积极正向引导
    assert "积极" in prompt or "正向" in prompt


def test_system_prompt_contains_utility_accuracy_rules():
    """实用层：知识问题要严谨准确、不编造。"""
    prompt = build_system_prompt(personality="博学多才")
    assert "准确" in prompt or "严谨" in prompt
    assert "不编造" in prompt or "不确定" in prompt or "坦诚" in prompt


def test_system_prompt_includes_custom_persona():
    """人设层：用户自定义 persona 必须被纳入。"""
    custom = "你叫小暖，说话带‘呀’和‘呢’，喜欢用比喻。"
    prompt = build_system_prompt(persona_prompt=custom)
    assert "小暖" in prompt
    assert "比喻" in prompt


def test_system_prompt_includes_companion_name():
    """伴侣名字应出现在人设层。"""
    prompt = build_system_prompt(companion_name="小暖")
    assert "小暖" in prompt


def test_system_prompt_contains_safety_guidance():
    """安全底线：遇危机信号给出求助建议。"""
    prompt = build_system_prompt()
    assert "求助" in prompt or "专业" in prompt or "危机" in prompt


# ---------- build_avatar_prompt ----------

def test_avatar_prompt_contains_style_locking_prefix():
    """画风锁定词前缀，保证风格统一。"""
    prompt = build_avatar_prompt(personality="温柔体贴", description="可爱女孩")
    assert "动漫" in prompt
    assert "高清" in prompt or "高质量" in prompt


def test_avatar_prompt_includes_selected_style_keywords():
    """不同风格预设应注入不同关键词。"""
    healing = build_avatar_prompt(
        personality="温柔体贴", description="可爱女孩", style="anime_healing"
    )
    cyber = build_avatar_prompt(
        personality="酷炫个性", description="未来感", style="cyberpunk"
    )
    # 两个风格产出的提示词应有差异
    assert healing != cyber
    assert "治愈" in healing or "柔和" in healing or "温暖" in healing
    assert "赛博" in cyber or "霓虹" in cyber or "未来" in cyber


def test_avatar_prompt_includes_character_traits():
    """人物设定（性别/发色/瞳色/服装）应注入提示词。"""
    prompt = build_avatar_prompt(
        personality="温柔体贴",
        description="可爱女孩",
        gender="female",
        hair_color="粉色长发",
        eye_color="蓝色瞳孔",
        outfit="白色连衣裙",
    )
    assert "粉色长发" in prompt
    assert "蓝色瞳孔" in prompt
    assert "白色连衣裙" in prompt


def test_avatar_prompt_handles_missing_optional_fields():
    """可选字段缺失时应正常生成（不报错、仍有画风+描述）。"""
    prompt = build_avatar_prompt(personality="温柔体贴", description="可爱女孩")
    assert "可爱女孩" in prompt
    assert "动漫" in prompt
