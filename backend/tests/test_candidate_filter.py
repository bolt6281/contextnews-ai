from app.candidate_filter import NewsArticle, candidate_filter, filter_candidate_articles


def test_candidate_filter_returns_matched_keywords():
    article = NewsArticle(
        title="반도체 공급망 재편",
        url="https://example.com/news/2",
        source="Example",
        description="<p>AI 칩과 메모리 수요가 늘고 있습니다.</p>",
    )

    result = candidate_filter(article, ["AI 칩", "배터리"])

    assert result.accepted is True
    assert result.matched_keywords == ["AI 칩"]


def test_candidate_filter_rejects_articles_without_keyword_matches():
    article = NewsArticle(
        title="여행 수요 증가",
        url="https://example.com/news/3",
        source="Example",
        description="<p>연휴 항공권 판매가 늘었습니다.</p>",
    )

    result = candidate_filter(article, ["AI", "반도체"])

    assert result.accepted is False
    assert result.matched_keywords == []


def test_filter_candidate_articles_keeps_only_matches():
    articles = [
        NewsArticle(title="AI 투자 확대", url="https://example.com/1", source="Example"),
        NewsArticle(title="여행 수요 증가", url="https://example.com/2", source="Example"),
    ]

    candidates = filter_candidate_articles(articles, ["AI"])

    assert len(candidates) == 1
    assert candidates[0].article.url == "https://example.com/1"
