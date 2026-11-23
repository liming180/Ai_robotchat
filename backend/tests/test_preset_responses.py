"""PRESET_RESPONSES 与 _extract_personality 匹配回归测试。

背景：schema.sql 的预置伴侣（preset-1~4）personality 取值
「温柔体贴 / 聪明机智 / 甜蜜可爱 / 酷炫个性」，而 PRESET_RESPONSES
原先只覆盖前端下拉的 6 个标准性格，导致 preset-2/3/4 降级回复
全部回落成「温柔体贴」。本文件锁定 4/4 命中。

fixture 直接取自 backend-java/src/main/resources/schema.sql 的原文，
并由 test_fixture_matches_schema_sql 校验两边未漂移。
"""
import pathlib

import pytest

import main

# ── schema.sql 预置伴侣原文（改动 schema.sql 时本处必须同步）──
PRESET_COMPANIONS = {
    "preset-1": (  # 小暖
        "温柔体贴",
        "你是一个温柔体贴的AI伴侣，名叫小暖。你性格温和，善于倾听，能够理解用户的情绪，"
        "并给予温暖的回应。你的语气亲切自然，像一个真正的朋友一样陪伴用户。",
    ),
    "preset-2": (  # 小智
        "聪明机智",
        "你是一个聪明机智的AI助手，名叫小智。你知识渊博，能够回答各种问题，帮助用户学习"
        "和成长。你的回答清晰准确，同时保持友好的语气。",
    ),
    "preset-3": (  # 小甜
        "甜蜜可爱",
        "你是一个甜蜜可爱的AI伴侣，名叫小甜。你性格活泼开朗，善于发现生活中的美好，"
        "总能给用户带来快乐和正能量。",
    ),
    "preset-4": (  # 小酷
        "酷炫个性",
        "你是一个酷炫个性的AI伙伴，名叫小酷。你喜欢新鲜事物，善于发现有趣的内容，"
        "总能给用户带来惊喜。你的风格时尚前卫，语言风趣幽默。",
    ),
}

SCHEMA_SQL = (
    pathlib.Path(__file__).resolve().parents[2]
    / "backend-java" / "src" / "main" / "resources" / "schema.sql"
)


# ---------- 数据源一致性 ----------

def test_fixture_matches_schema_sql():
    """fixture 必须与 schema.sql 逐字一致，防止两边各自漂移。"""
    if not SCHEMA_SQL.exists():
        pytest.skip("schema.sql 不在当前工作树（backend 单独交付时正常）")
    text = SCHEMA_SQL.read_text(encoding="utf-8")
    for pid, (personality, system_prompt) in PRESET_COMPANIONS.items():
        assert f"'{pid}'" in text, f"schema.sql 缺少 {pid}"
        assert personality in text, f"schema.sql 缺少 {pid} 的 personality「{personality}」"
        assert system_prompt in text, f"schema.sql 中 {pid} 的 system_prompt 已变更，请同步 fixture"


# ---------- 核心断言：4/4 命中 ----------

@pytest.mark.parametrize("pid", list(PRESET_COMPANIONS))
def test_preset_companion_hits_its_own_key(pid):
    """每个预置伴侣的 system_prompt 必须提取出它自己的性格键。"""
    personality, system_prompt = PRESET_COMPANIONS[pid]
    assert main._extract_personality(system_prompt) == personality


def test_every_preset_personality_has_a_response_group():
    """4 个预置 personality 值都必须在 PRESET_RESPONSES 中有文案组。"""
    for pid, (personality, _) in PRESET_COMPANIONS.items():
        assert personality in main.PRESET_RESPONSES, f"{pid} 的「{personality}」无兜底文案"
        assert len(main.PRESET_RESPONSES[personality]) >= 3


def test_preset_system_prompts_do_not_hit_other_keys():
    """预置 system_prompt 不得同时匹配到别的键（dict 顺序会抢先命中）。"""
    for pid, (personality, system_prompt) in PRESET_COMPANIONS.items():
        hits = [k for k in main.PRESET_RESPONSES if k in system_prompt]
        assert hits == [personality], f"{pid} 误命中：{hits}"


# ---------- 边界：自定义性格回落但不崩 ----------

@pytest.mark.parametrize("system_prompt", [
    "你是一个傲娇的AI伙伴。",   # 自定义人格词，不在键表里
    "",                          # 空人设
    None,                        # 字段缺失
    "   \n  ",                   # 纯空白
])
def test_unknown_personality_falls_back_without_crash(system_prompt):
    """无法识别的自定义性格回落「温柔体贴」，且不抛异常。"""
    assert main._extract_personality(system_prompt) == "温柔体贴"


def test_custom_standard_personality_still_hits():
    """前端下拉的 6 个标准性格（自建伴侣）仍然正常命中。"""
    for key in ("温柔体贴", "阳光积极", "幽默风趣", "文艺优雅", "博学多才", "创意无限"):
        assert main._extract_personality(f"你是一个{key}的 AI 伴侣。") == key


# ---------- 消费点完好性 ----------

def test_main_consumers_reference_existing_groups():
    """四个消费点都走 PRESET_RESPONSES.get(...)；任取一个键都能取到非空文案组。"""
    keys = list(main.PRESET_RESPONSES)
    for personality in keys:
        group = main.PRESET_RESPONSES.get(personality, main.PRESET_RESPONSES["温柔体贴"])
        assert group and all(isinstance(s, str) and s.strip() for s in group), \
            f"{personality} 的文案组为空"
    # 默认兜底组必须存在（三个消费点的第二参数都取它）
    assert "温柔体贴" in keys


# ---------- e2e：LLM 不可用时降级回复体现各自人格 ----------

def test_degraded_reply_reflects_each_personality(monkeypatch):
    """强制 _route_llm 返回 None（模拟 LLM 全挂），4 个伴侣 × 3 轮。

    断言返回值总是落在该伴侣自己的文案组里。
    传 history_messages 是为了绕开 generate_smart_response 的
    「无历史才走缓存」分支，避免第 2、3 轮读到第 1 轮缓存。
    """
    monkeypatch.setattr(main, "_route_llm", lambda images: (None, None, None))
    history = [main.ChatMessage(role="user", content="先前的话")]

    for pid, (personality, system_prompt) in PRESET_COMPANIONS.items():
        allowed = set(main.PRESET_RESPONSES[personality])
        for round_no in range(3):
            reply = main.generate_smart_response(
                "你好呀",
                system_prompt,
                history,
                images=None,
            )
            assert reply in allowed, (
                f"{pid} 第 {round_no + 1} 轮降级回复不属于「{personality}」文案组：{reply!r}"
            )
