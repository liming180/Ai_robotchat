"""
JSON 解析器（零依赖，点号路径提取）。

不引入 jq / pyjq（Windows + Python 3.12 编译易失败），改用点号路径。

parser_config 结构：
    {
      "itemsPath":    "data.list",   # 可省略；指向数组或对象
      "contentField": "text",        # 必填；内容字段，支持点号路径
      "titleField":   "title",       # 可选；标题字段
      "metaFields":   ["id", "tag"]  # 可选；额外保留的元数据字段
    }

约定：
- 若 itemsPath 指向数组，则每个元素解析为一条知识；
- 若指向对象或省略，则整体作为一条知识；
- contentField 取不到值时，退化为把该对象序列化为 JSON 文本。
"""

import json
from typing import Any, Dict, List, Optional

from app.parsers.base import BaseParser, ParsedItem


def _get_by_path(obj: Any, path: Optional[str]) -> Any:
    """按点号路径取值，例如 "data.list" / "title"。取不到返回 None。"""
    if not path:
        return None
    cur = obj
    for seg in path.split("."):
        seg = seg.strip()
        if not seg:
            continue
        if isinstance(cur, dict):
            if seg not in cur:
                return None
            cur = cur[seg]
        elif isinstance(cur, list):
            # 支持 "list.0.name" 这类下标
            if not seg.isdigit():
                return None
            idx = int(seg)
            if idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            return None
    return cur


class JsonParser(BaseParser):
    """JSON 解析器。"""

    def parse(
        self,
        raw: str,
        default_title: str = "未命名",
        parser_config: Optional[Dict[str, Any]] = None,
    ) -> List[ParsedItem]:
        text = (raw or "").strip()
        if not text:
            return []

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败：{e.msg} (行 {e.lineno} 列 {e.colno})")

        cfg = parser_config or {}
        items_path = cfg.get("itemsPath")
        content_field = cfg.get("contentField") or "content"
        title_field = cfg.get("titleField")
        meta_fields = cfg.get("metaFields") or []

        target = _get_by_path(data, items_path) if items_path else data
        if target is None:
            raise ValueError(f"itemsPath 未取到数据：{items_path}")

        # 统一成列表处理
        if isinstance(target, list):
            records = target
        else:
            records = [target]

        items: List[ParsedItem] = []
        for i, rec in enumerate(records):
            if rec is None:
                continue

            # 内容
            content = _get_by_path(rec, content_field)
            if content is None and isinstance(rec, str):
                content = rec
            if content is None:
                content = json.dumps(rec, ensure_ascii=False)
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            content = content.strip()
            if not content:
                continue

            # 标题
            title = _get_by_path(rec, title_field) if title_field else None
            if not isinstance(title, str) or not title.strip():
                title = f"{default_title} #{i + 1}" if len(records) > 1 else default_title

            # 额外元数据
            meta: Dict[str, Any] = {"recordIndex": i}
            for f in meta_fields:
                v = _get_by_path(rec, f)
                if isinstance(v, (str, int, float, bool)):
                    meta[f] = v

            items.append(ParsedItem(title=title.strip(), content=content, meta=meta))

        return items
