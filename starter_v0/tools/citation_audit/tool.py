from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def _has_http_url(value: Any) -> bool:
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def citation_audit(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = items or []
    issues: list[dict[str, Any]] = []
    citation_ready_count = 0

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            issues.append({"index": index, "issues": ["item_not_object"]})
            continue

        item_issues: list[str] = []
        if not _has_http_url(item.get("url")):
            item_issues.append("missing_valid_url")
        if not str(item.get("source") or "").strip():
            item_issues.append("missing_source")
        if not (str(item.get("title") or "").strip() or str(item.get("summary") or "").strip()):
            item_issues.append("missing_title_or_summary")

        if item_issues:
            issues.append({
                "index": index,
                "title": item.get("title") or "",
                "issues": item_issues,
            })
        else:
            citation_ready_count += 1

    return {
        "tool": "citation_audit",
        "item_count": len(items),
        "citation_ready_count": citation_ready_count,
        "issues": issues,
        "passed": not issues,
    }
