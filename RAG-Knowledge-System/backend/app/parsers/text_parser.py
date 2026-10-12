"""
纯文本 / Markdown 解析器。

策略：
- .txt：整篇作为一条知识，标题用文件名；
- .md ：若存在 Markdown 标题（# / ## / ###），按标题切分为多条，
        每条标题作为 title；没有标题则退化为整篇一条。
"""

import re
from typing import Any, Dict, List, Optional

from app.parsers.base import BaseParser, ParsedItem

# 匹配 1~3 级标题
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)


class TextParser(BaseParser):
    """txt / md 通用解析器。"""

    def parse(
        self,
        raw: str,
        default_title: str = "未命名",
        parser_config: Optional[Dict[str, Any]] = None,
    ) -> List[ParsedItem]:
        text = (raw or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not text:
            return []

        # 按 Markdown 标题切分（txt 通常没有 #，会自然退化为整篇一条）
        matches = list(_HEADING_RE.finditer(text))
        if not matches:
            return [ParsedItem(title=default_title, content=text)]

        items: List[ParsedItem] = []
        # 第一个标题之前的内容（前言）
        preamble = text[: matches[0].start()].strip()
        if preamble:
            items.append(ParsedItem(title=default_title, content=preamble))

        for i, m in enumerate(matches):
            title = m.group(2).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            if not body:
                continue
            items.append(
                ParsedItem(
                    title=title or default_title,
                    content=body,
                    meta={"headingLevel": len(m.group(1))},
                )
            )

        # 标题解析后一条都没有（例如全是空标题），退化为整篇
        return items or [ParsedItem(title=default_title, content=text)]
