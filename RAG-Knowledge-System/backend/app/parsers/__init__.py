"""
文件解析器注册表。

用法：
    parser = get_parser("md")
    items = parser.parse(raw_text, default_title="话术", parser_config=None)
"""

from typing import Optional

from app.parsers.base import BaseParser, ParsedItem
from app.parsers.json_parser import JsonParser
from app.parsers.text_parser import TextParser

__all__ = ["BaseParser", "ParsedItem", "get_parser", "SUPPORTED_EXTENSIONS"]

# txt 与 md 共用 TextParser
_PARSERS = {
    "txt": TextParser(),
    "md": TextParser(),
    "json": JsonParser(),
}

SUPPORTED_EXTENSIONS = tuple(_PARSERS.keys())


def get_parser(ext: str) -> Optional[BaseParser]:
    """按扩展名取解析器；不支持返回 None。"""
    return _PARSERS.get((ext or "").lower().lstrip("."))
