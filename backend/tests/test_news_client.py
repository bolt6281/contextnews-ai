from app.news_client import (
    NewsArticle,
    build_google_news_rss_url,
    fetch_news,
    parse_rss_feed,
)


def test_google_news_rss_url_uses_keyword_and_lookback_without_api_key():
    url = build_google_news_rss_url("인공지능", lookback_days=3)

    assert url.startswith("https://news.google.com/rss/search?")
    assert "q=%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5+when%3A3d" in url
    assert "key=" not in url.lower()
    assert "api_key" not in url.lower()


def test_parse_rss_feed_normalizes_items_and_strips_html():
    xml_text = """
    <rss>
      <channel>
        <item>
          <title><![CDATA[AI <b>뉴스</b>]]></title>
          <link>https://example.com/news/1</link>
          <source>Example</source>
          <description><![CDATA[<p>본문 &amp; 설명</p>]]></description>
          <pubDate>Mon, 11 May 2026 12:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    articles = parse_rss_feed(xml_text)

    assert articles == [
        NewsArticle(
            title="AI 뉴스",
            url="https://example.com/news/1",
            source="Example",
            description="본문 & 설명",
            published_at="2026-05-11T12:00:00Z",
        )
    ]


def test_sample_provider_does_not_call_external_service():
    articles = fetch_news("sample", keyword="기후", lookback_days=2, limit=1)

    assert len(articles) == 1
    assert "기후" in articles[0].title
