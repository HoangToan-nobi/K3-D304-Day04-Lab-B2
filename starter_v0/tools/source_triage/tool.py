from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


TRUSTED_DOMAINS = {
    "acm.org",
    "anthropic.com",
    "arxiv.org",
    "developer.x.com",
    "docs.github.com",
    "docs.tavily.com",
    "firecrawl.dev",
    "github.com",
    "nature.com",
    "openai.com",
    "science.org",
}


LOW_SIGNAL_DOMAINS = {
    "medium.com",
    "reddit.com",
    "substack.com",
    "x.com",
    "twitter.com",
}


def _domain(url: str) -> str:
    host = urlparse(url or "").netloc.lower()
    return host.removeprefix("www.")


def _score(item: dict[str, Any], query_terms: set[str]) -> tuple[int, list[str]]:
    score = 0
    flags: list[str] = []
    domain = _domain(str(item.get("url") or ""))
    haystack = " ".join(str(item.get(key) or "").lower() for key in ("title", "summary", "source"))

    if domain in TRUSTED_DOMAINS or any(domain.endswith("." + trusted) for trusted in TRUSTED_DOMAINS):
        score += 3
        flags.append("trusted_domain")
    elif domain in LOW_SIGNAL_DOMAINS or any(domain.endswith("." + low) for low in LOW_SIGNAL_DOMAINS):
        score -= 1
        flags.append("low_signal_domain")

    if item.get("url"):
        score += 1
    else:
        flags.append("missing_url")

    if item.get("date"):
        score += 1
    else:
        flags.append("missing_date")

    term_hits = sum(1 for term in query_terms if term in haystack)
    score += min(3, term_hits)
    if query_terms and term_hits == 0:
        flags.append("weak_query_match")

    return score, flags


def source_triage(
    items: list[dict[str, Any]] | None = None,
    query: str = "",
    max_items: int = 8,
) -> dict[str, Any]:
    items = items or []
    query_terms = {part.lower() for part in query.split() if len(part) > 2}
    ranked: list[dict[str, Any]] = []
    warnings: list[str] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        score, flags = _score(item, query_terms)
        enriched = dict(item)
        enriched["triage_score"] = score
        enriched["triage_flags"] = flags
        ranked.append(enriched)

    ranked.sort(key=lambda item: item.get("triage_score", 0), reverse=True)
    output = ranked[: max(1, int(max_items or 8))]

    if any("low_signal_domain" in item.get("triage_flags", []) for item in output):
        warnings.append("Some selected items are from social or user-generated domains; cite cautiously.")
    if any("missing_url" in item.get("triage_flags", []) for item in output):
        warnings.append("Some selected items have no URL; avoid presenting them as independently verifiable.")

    return {
        "tool": "source_triage",
        "items": output,
        "input_count": len(items),
        "output_count": len(output),
        "warnings": warnings,
    }
