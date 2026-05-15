from __future__ import annotations

import html
import re
from typing import Any


KEYWORD_RE = re.compile(r"[0-9A-Za-z가-힣]{2,}")
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    without_tags = HTML_TAG_RE.sub(" ", value)
    unescaped = html.unescape(without_tags)
    return WHITESPACE_RE.sub(" ", unescaped).strip()


def unique_values(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in unique:
            unique.append(normalized)
    return unique


class MockAIAdapter:
    def generate_hidden_keywords(self, keyword: str, additional_description: str = "") -> dict[str, Any]:
        description_keywords = KEYWORD_RE.findall(strip_html(additional_description))
        hidden_keywords = unique_values([keyword, *description_keywords])

        return {
            "hidden_keywords": hidden_keywords,
            "provider": "mock",
        }

    def judge_candidate(self, article: dict[str, Any], matched_keywords: list[str]) -> dict[str, Any]:
        accepted = bool(matched_keywords)
        return {
            "accepted": accepted,
            "matched_keywords": matched_keywords,
            "reason": "matched_keywords 기준으로 후보로 분류됨" if accepted else "매칭된 키워드가 없어 제외됨",
            "article_url": article.get("url", ""),
        }

    def summarize(self, article: dict[str, Any]) -> dict[str, Any]:
        title = strip_html(article.get("title", ""))
        source = strip_html(article.get("source", ""))
        description = strip_html(article.get("description", ""))
        summary = description or title

        return {
            "summary": summary,
            "bullet_points": [
                f"제목: {title}",
                f"출처: {source or 'unknown'}",
                f"요약: {summary}",
            ],
        }

    def analyze_candidate(self, article: dict[str, Any], matched_keywords: list[str]) -> dict[str, Any]:
        return {
            "decision": self.judge_candidate(article, matched_keywords),
            "summary": self.summarize(article),
        }
