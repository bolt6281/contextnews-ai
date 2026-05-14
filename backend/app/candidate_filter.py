from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .text_utils import normalize_for_match


@dataclass(frozen=True)
class CandidateArticle:
    article: object
    matched_keywords: list[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return bool(self.matched_keywords)


def candidate_filter(article: object, hidden_keywords: Iterable[str]) -> CandidateArticle:
    title = getattr(article, "title", "")
    description = getattr(article, "description", "")
    searchable_text = normalize_for_match(f"{title} {description}")
    matched_keywords = [
        keyword.strip()
        for keyword in hidden_keywords
        if keyword and keyword.strip() and keyword.strip().casefold() in searchable_text
    ]
    return CandidateArticle(article=article, matched_keywords=matched_keywords)


def filter_candidate_articles(
    articles: Iterable[object],
    hidden_keywords: Iterable[str],
) -> list[CandidateArticle]:
    keyword_list = list(hidden_keywords)
    return [
        candidate
        for article in articles
        if (candidate := candidate_filter(article, keyword_list)).accepted
    ]
