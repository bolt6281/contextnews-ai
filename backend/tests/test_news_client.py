import asyncio
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.news_client import _build_google_news_url, _parse_google_item, fetch_news
from app.services.sample_data import sample_news


def test_parse_google_item_normalizes_news_fields():
    item = ET.fromstring(
        """
        <item>
          <title><![CDATA[AI <b>뉴스</b>]]></title>
          <link>https://example.com/news/1</link>
          <source>Example</source>
          <description><![CDATA[<p>본문 &amp; 설명</p>]]></description>
          <pubDate>Mon, 11 May 2026 12:00:00 GMT</pubDate>
        </item>
        """
    )

    article = _parse_google_item(item)

    assert article["title"] == "AI 뉴스"
    assert article["url"] == "https://example.com/news/1"
    assert article["source"] == "Example"
    assert article["description"] == "본문 & 설명"
    assert article["published_at"] == "2026-05-11T12:00:00Z"
    assert "raw_payload" in article


def test_google_news_url_does_not_require_api_key():
    url = _build_google_news_url("인공지능", lookback_days=3)

    assert url.startswith("https://news.google.com/rss/search?")
    assert "q=%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5+when%3A3d" in url
    assert "key=" not in url.lower()
    assert "api_key" not in url.lower()


def test_sample_news_returns_three_articles_with_raw_payload():
    articles = sample_news()

    assert len(articles) == 3
    assert all(article["source"] == "Sample News" for article in articles)
    assert all(article["raw_payload"] for article in articles)


def test_fetch_news_uses_sample_provider_for_local_checks():
    articles = asyncio.run(fetch_news("AI", limit=2, provider="sample"))

    assert len(articles) == 2
    assert articles[0]["title"] == "AI 반도체 공급망 재편"
