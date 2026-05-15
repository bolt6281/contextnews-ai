from __future__ import annotations

import html
import re
from typing import Any


HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    without_tags = HTML_TAG_RE.sub(" ", value)
    unescaped = html.unescape(without_tags)
    return WHITESPACE_RE.sub(" ", unescaped).strip()


def normalize_for_match(value: str | None) -> str:
    return strip_html(value).casefold()


def candidate_filter(article: dict[str, Any], hidden_keywords: list[str]) -> dict[str, Any]:
    searchable_text = normalize_for_match(
        f"{article.get('title', '')} {article.get('description', '')} {article.get('summary', '')}"
    )
    matched_keywords = [
        keyword.strip()
        for keyword in hidden_keywords
        if keyword and keyword.strip() and keyword.strip().casefold() in searchable_text
    ]

    return {
        "accepted": bool(matched_keywords),
        "matched_keywords": matched_keywords,
        "article": {
            **article,
            "title": strip_html(article.get("title", "")),
            "description": strip_html(article.get("description", "")),
        },
    }


def filter_candidates(articles: list[dict[str, Any]], hidden_keywords: list[str]) -> list[dict[str, Any]]:
    return [
        result
        for article in articles
        if (result := candidate_filter(article, hidden_keywords))["accepted"]
    ]
