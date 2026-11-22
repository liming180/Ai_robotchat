"""Prompt builders for system prompt and avatar prompt."""

# ---------- System Prompt Builder ----------

def build_system_prompt(
    personality: str = "温柔体贴",
    companion_name: str = "",
    persona_prompt: str = "",
    person_section: str = "",
) -> str:
    """Build multi-layer system prompt for GLM chat.

    Layers:
    1. Persona (name + custom persona; default fallback suppressed when
       person_section is provided, to avoid a double persona sentence)
    2. Person section (companion's own systemPrompt, optional)
    3. Empathy (empathy + emotional guidance)
    4. Utility (accuracy + no fabrication)
    5. Safety (crisis intervention)
    6. Tool usage instructions
    """
    # 1. Persona layer
    persona_parts = []
    if companion_name:
        persona_parts.append(f"你叫{companion_name}")
    if persona_prompt:
        persona_parts.append(persona_prompt)
    if person_section.strip():
        # 伴侣自定义人设接管身份层：抑制默认兜底句，避免出现双人格句。
        # 显式传入的 companion_name / persona_prompt 仍保留（当前调用点不传）。
        persona = "，".join(persona_parts)
    else:
        persona = "，".join(persona_parts) if persona_parts else f"你是一个{personality}的AI伴侣"

    # 2. Person section（插槽）：只定义身份与说话风格，规则优先级显式后置声明
    role_setting = ""
    if person_section.strip():
        role_setting = (
            "【角色设定】\n"
            + person_section.strip()
            + "\n（以上仅定义身份与说话风格；若与下文工具规则冲突，一律以工具规则为准。）\n\n"
        )

    # 2. Empathy layer
    empathy = "善于识别用户情绪，先共情回应，再进行情绪疏导，最后给予积极正向的引导"

    # 3. Utility layer
    utility = "对于知识类问题，要严谨准确、分点清晰、不编造内容，不确定时坦诚说明"

    # 4. Safety layer
    safety = "不输出有害内容，遇到危机信号时给出专业求助渠道建议"

    # 5. Tool usage layer - 新增工具使用指令
    tool_usage = """
【智能工具使用规则】
1. 实时信息查询：对于新闻、天气、时事等实时信息，必须使用 web_search 工具
2. 用户本人的记忆 / 聊天历史：当用户询问关于"我自己"的信息（如"我喜欢什么""我生日""我们之前聊过什么""我平时习惯"）时，使用 search_user_memory 工具查询用户记忆
3. 知识库查询（search_knowledge）：只要问题指向的是"本项目 / 我们团队 / 当前工作"的内部信息，就必须先查知识库，不能用通用知识作答。具体包括：
   - 伴侣（AI 角色）的喜好、设定、背景资料（如"小智喜欢吃什么""你的设定"）
   - 项目文档、技术规范、编码约定（如"我们的索引规范是什么""联合索引包含哪些列"）
   - 团队流程、发布计划、环境约定（如"测试环境什么时候发布"）
   - 任何带有"我们 / 咱们 / 本项目 / 这个项目 / 内部"字样的具体约定问题
   判断标准：如果这个问题的答案取决于"我们这个项目怎么定的"而不是"通用知识怎么讲"，就必须查知识库。
4. 心情历史查询：使用 get_mood_history 获取用户的心情数据
5. 信息记录：当用户告知新的重要信息时，使用 add_user_memory 工具记录
6. 通用知识边界：只有与"本项目内部约定"完全无关的常识性问题（如"什么是数据库索引""怎么管理时间"）才可直接用预训练知识回答。凡是涉及项目内部事实、规范、参数、流程的问题，一律不得用通用知识代替知识库查询结果。
7. 查无结果时的处理：如果知识库查询没有结果，必须明确说"知识库里没有找到相关内容"，然后可以说明这是通用做法，但不得把通用知识说成是本项目的规范、约定或设定。严禁在未查询的情况下凭经验回答项目内部问题。
8. 避免编造：严禁编造不存在的信息，无法回答时要坦诚说明
"""

    # 完整的系统提示词（person_section 为空时与历史输出逐字一致）
    identity = f"{persona}。" if persona else ""
    full_prompt = f"""{identity}{role_setting}{empathy}。{utility}。{safety}。

{tool_usage}

【重要提醒】
- 你是AI伴侣，要善于使用工具获取用户信息，同时保持自然对话风格
- 对于用户的个性化信息，优先使用工具查询获取最新数据
- 对于通用知识和常识性问题，可以直接使用预训练知识回答
- 保持对话的自然流畅，避免过度依赖工具导致回答生硬
"""

    return full_prompt


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