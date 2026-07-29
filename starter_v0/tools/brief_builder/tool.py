from __future__ import annotations

from typing import Any


def _line(item: dict[str, Any]) -> str:
    title = str(item.get("title") or item.get("summary") or "Untitled").strip()
    source = str(item.get("source") or "").strip()
    url = str(item.get("url") or "").strip()
    suffix = f" - {source}" if source else ""
    link = f" ({url})" if url else ""
    return f"- {title}{suffix}{link}"


def brief_builder(
    items: list[dict[str, Any]] | None = None,
    audience: str = "demo reviewers",
    objective: str = "summarize the most relevant findings",
    max_items: int = 5,
) -> dict[str, Any]:
    items = [item for item in (items or []) if isinstance(item, dict)]
    selected = items[: max(1, int(max_items or 5))]
    lines = [
        f"Audience: {audience or 'demo reviewers'}",
        f"Objective: {objective or 'summarize the most relevant findings'}",
        "",
        "Key points:",
        *[_line(item) for item in selected],
    ]
    return {
        "tool": "brief_builder",
        "brief": "\n".join(lines),
        "item_count": len(items),
        "included_count": len(selected),
    }
