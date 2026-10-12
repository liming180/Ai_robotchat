"""
解析器基类与数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedItem:
    """解析出的一条知识。"""

    title: str
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    """所有解析器的抽象基类。"""

    @abstractmethod
    def parse(
        self,
        raw: str,
        default_title: str = "未命名",
        parser_config: Optional[Dict[str, Any]] = None,
    ) -> List[ParsedItem]:
        """把原始文本解析为若干条知识。

        Args:
            raw: 文件解码后的文本内容。
            default_title: 无法从内容中提取标题时的兜底标题（通常是文件名）。
            parser_config: 集合级解析规则，JSON 文件使用。

        Returns:
            ParsedItem 列表；解析不出内容时返回空列表。
        """
        raise NotImplementedError
