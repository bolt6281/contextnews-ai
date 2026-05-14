import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.candidate_filter import candidate_filter, filter_candidates


def test_candidate_filter_accepts_when_hidden_keyword_matches_title():
    article = {
        "title": "AI 반도체 공급망 재편",
        "url": "https://example.com/news/1",
        "description": "시장 변화가 커지고 있습니다.",
    }

    result = candidate_filter(article, ["반도체", "배터리"])

    assert result["accepted"] is True
    assert result["matched_keywords"] == ["반도체"]


def test_candidate_filter_accepts_when_hidden_keyword_matches_description_without_html():
    article = {
        "title": "데이터센터 투자 확대",
        "url": "https://example.com/news/2",
        "description": "<p>AI 칩과 전력 인프라 수요가 증가했습니다.</p>",
    }

    result = candidate_filter(article, ["AI 칩", "전력"])

    assert result["accepted"] is True
    assert result["matched_keywords"] == ["AI 칩", "전력"]
    assert result["article"]["description"] == "AI 칩과 전력 인프라 수요가 증가했습니다."


def test_candidate_filter_rejects_without_keyword_matches():
    article = {
        "title": "여행 수요 증가",
        "url": "https://example.com/news/3",
        "description": "항공권 판매가 늘었습니다.",
    }

    result = candidate_filter(article, ["AI", "반도체"])

    assert result["accepted"] is False
    assert result["matched_keywords"] == []


def test_filter_candidates_returns_only_accepted_results():
    articles = [
        {"title": "AI 투자 확대", "url": "https://example.com/1", "description": ""},
        {"title": "여행 수요 증가", "url": "https://example.com/2", "description": ""},
    ]

    results = filter_candidates(articles, ["AI"])

    assert len(results) == 1
    assert results[0]["article"]["url"] == "https://example.com/1"
