"""列表项切块（_split_list_items）单元测试。

覆盖三类真实语料误切（2026-11-23 codex 审计发现）：
- 代码围栏内的 -/+/* 行（diff / yaml / c 注释）
- 嵌套列表（子项不得脱离父项单独成块）
- 年份句点（2024. 年…）与水平分割线（- - - / * * *）

以及「0/1 个顶层列表项时与原逻辑逐字节一致」的兜底约束。
运行：在 RAG-Knowledge-System/backend 下 `python -m pytest tests/test_ingest_split.py -q`
"""
import pytest

from app.workers.ingest import _split_list_items


# ---------- 正常切分 ----------

def test_flat_bullets_split_into_one_piece_each():
    content = "前言\n- 第一条\n- 第二条\n- 第三条"
    assert _split_list_items(content) == ["前言", "- 第一条", "- 第二条", "- 第三条"]


def test_ordered_list_supported():
    content = "步骤：\n1. 打开\n2) 关闭"
    assert _split_list_items(content) == ["步骤：", "1. 打开", "2) 关闭"]


# ---------- 不应切分 ----------

def test_single_item_returns_content_unchanged():
    content = "只有一条\n- 唯一要点\n后续说明"
    assert _split_list_items(content) == [content]


def test_no_list_returns_content_unchanged():
    content = "第一段\n\n第二段"
    assert _split_list_items(content) == [content]


def test_table_rows_are_not_list_items():
    content = "| a | b |\n| --- | --- |\n| 1 | 2 |"
    assert _split_list_items(content) == [content]


def test_horizontal_rules_are_not_list_items():
    content = "标题\n- - -\n正文一\n* * *\n正文二"
    assert _split_list_items(content) == [content]


def test_year_with_period_is_not_list_item():
    content = "回顾：\n2024. 年销量增长 30%\n2025. 年继续增长"
    assert _split_list_items(content) == [content]


# ---------- 代码围栏 ----------

def test_diff_fence_is_not_split():
    content = "修改补丁如下：\n```diff\n- old line here\n+ new line here\n```\n请按补丁执行。"
    assert _split_list_items(content) == [content]


def test_yaml_fence_is_not_split():
    content = "配置：\n```yaml\n- name: alpha\n- name: beta\n```\n完成。"
    assert _split_list_items(content) == [content]


def test_c_comment_fence_is_not_split():
    content = "示例：\n```c\n * 注释 a\n * 注释 b\n```\n结束。"
    assert _split_list_items(content) == [content]


def test_bullets_outside_fence_still_split():
    content = "- 第一条\n```text\n- 围栏内\n- 围栏内二\n```\n- 第二条"
    assert _split_list_items(content) == [
        "- 第一条\n```text\n- 围栏内\n- 围栏内二\n```",
        "- 第二条",
    ]


def test_unclosed_fence_returns_content_unchanged():
    """围栏未闭合时无法可靠判断边界，安全降级为不切分。"""
    content = "```text\n- 一\n- 二"
    assert _split_list_items(content) == [content]


def test_four_backtick_fence_wraps_inner_three_backticks():
    """```` 包 ``` 时，内层 ``` 不得提前关闭围栏。"""
    content = "````md\n```\n- x\n- y\n```\n````"
    assert _split_list_items(content) == [content]


# ---------- 嵌套列表 ----------

def test_nested_children_follow_parent():
    content = "- 日志\n  - 级别用 info\n  - 输出到 stdout\n- 错误\n  - 必须带堆栈"
    assert _split_list_items(content) == [
        "- 日志\n  - 级别用 info\n  - 输出到 stdout",
        "- 错误\n  - 必须带堆栈",
    ]


def test_uniformly_indented_bullets_still_split_on_min_indent():
    content = "  - 甲\n  - 乙"
    assert _split_list_items(content) == ["- 甲", "- 乙"]


def test_tab_indented_child_follows_parent():
    content = "- 日志\n\t- 子项一\n\t- 子项二\n- 错误"
    assert _split_list_items(content) == [
        "- 日志\n\t- 子项一\n\t- 子项二",
        "- 错误",
    ]


# ---------- _chunk 级：0/1 列表项与改动前逐字节等价 ----------

def test_chunk_without_multi_items_is_identical_to_plain_splitter():
    """无列表项或只有一个列表项时，_chunk 必须与直接跑 splitter 完全一致。"""
    from types import SimpleNamespace
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from app.parsers import ParsedItem
    from app.workers.ingest import _chunk

    coll = SimpleNamespace(chunk_size=500, chunk_overlap=50)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    for content in ("第一段。\n\n第二段。", "只有一条\n- 唯一要点\n后续说明"):
        item = ParsedItem(title="t", content=content)
        expected = [{"title": "t", "content": p.strip(), "item_meta": {}}
                    for p in splitter.split_text(content) if p.strip()]
        assert _chunk([item], coll) == expected


# ---------- 真实 fixture 回归 ----------

def test_fixture_08_still_splits_into_six_bullets():
    """08-preferences 是 6 条平铺 bullet，修复围栏/嵌套后仍必须切成 6 段。"""
    import pathlib

    path = (
        pathlib.Path(__file__).resolve().parent
        / "rag_regression" / "fixtures" / "a" / "08-preferences.md"
    )
    if not path.exists():
        pytest.skip("fixture 不在当前工作树")
    raw = path.read_text(encoding="utf-8")
    body = raw.split("\n", 1)[1].strip()  # 去掉 H1 标题行
    pieces = _split_list_items(body)
    assert len(pieces) == 6
    assert all(p.startswith("- ") for p in pieces)
    assert "FastAPI 和 PostgreSQL" in pieces[1]
