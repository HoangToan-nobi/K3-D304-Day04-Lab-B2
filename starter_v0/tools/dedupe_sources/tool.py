from __future__ import annotations

import re
from typing import Any


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip("/")


def _key(item: dict[str, Any]) -> str:
    url = _norm(item.get("url"))
    if url:
        return f"url:{url}"
    title = _norm(item.get("title"))
    source = _norm(item.get("source"))
    summary = _norm(item.get("summary"))[:120]
    return f"text:{source}:{title or summary}"


def dedupe_sources(items: list[dict[str, Any]] | None = None, max_items: int = 10) -> dict[str, Any]:
    items = items or []
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        key = _key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
        if len(deduped) >= max(1, int(max_items or 10)):
            break

    return {
        "tool": "dedupe_sources",
        "items": deduped,
        "input_count": len(items),
        "output_count": len(deduped),
        "removed_count": max(0, len(items) - len(deduped)),
    }
