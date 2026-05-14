from __future__ import annotations

from dataclasses import dataclass, field
import re

from .text_utils import strip_html


KEYWORD_RE = re.compile(r"[0-9A-Za-z가-힣]{2,}")


@dataclass(frozen=True)
class ArticleInput:
    title: str
    url: str
    source: str = ""
    description: str = ""


@dataclass(frozen=True)
class CandidateInput:
    article: ArticleInput
    matched_keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HiddenKeywordsResult:
    hidden_keywords: list[str]


@dataclass(frozen=True)
class CandidateDecision:
    accepted: bool
    matched_keywords: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class SummaryResult:
    summary: str
    bullet_points: list[str]


@dataclass(frozen=True)
class ArticleAnalysisResult:
    decision: CandidateDecision
    summary: SummaryResult


class TestAIAdapter:
    def generate_hidden_keywords(self, keyword: str, description: str) -> HiddenKeywordsResult:
        candidates = [keyword.strip()]
        candidates.extend(KEYWORD_RE.findall(strip_html(description)))

        hidden_keywords: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in hidden_keywords:
                hidden_keywords.append(candidate)

        return HiddenKeywordsResult(hidden_keywords=hidden_keywords)

    def judge_candidate(self, candidate: CandidateInput) -> CandidateDecision:
        accepted = bool(candidate.matched_keywords)
        reason = "matched_keywords 기준으로 후보로 분류됨" if accepted else "매칭된 키워드가 없어 제외됨"
        return CandidateDecision(
            accepted=accepted,
            matched_keywords=candidate.matched_keywords,
            reason=reason,
        )

    def summarize(self, article: ArticleInput) -> SummaryResult:
        description = strip_html(article.description)
        summary = description or article.title
        return SummaryResult(
            summary=summary,
            bullet_points=[
                f"제목: {article.title}",
                f"출처: {article.source or 'unknown'}",
                f"요약: {summary}",
            ],
        )

    def analyze_candidate(self, candidate: CandidateInput) -> ArticleAnalysisResult:
        return ArticleAnalysisResult(
            decision=self.judge_candidate(candidate),
            summary=self.summarize(candidate.article),
        )
