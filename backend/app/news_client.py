from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from .text_utils import strip_html


GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


@dataclass(frozen=True)
class NewsArticle:
    title: str
    url: str
    source: str
    description: str = ""
    published_at: str | None = None


def build_google_news_rss_url(keyword: str, lookback_days: int = 7) -> str:
    query = keyword.strip()
    if not query:
        raise ValueError("keyword is required")
    if lookback_days < 1:
        raise ValueError("lookback_days must be greater than 0")

    params = {
        "q": f"{query} when:{lookback_days}d",
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko",
    }
    return f"{GOOGLE_NEWS_RSS_URL}?{urlencode(params)}"


def normalize_rss_item(item: ET.Element) -> NewsArticle:
    source = item.find("source")
    return NewsArticle(
        title=strip_html(item.findtext("title")),
        url=(item.findtext("link") or "").strip(),
        source=strip_html(source.text if source is not None else ""),
        description=strip_html(item.findtext("description")),
        published_at=normalize_published_at(item.findtext("pubDate")),
    )


def normalize_published_at(value: str | None) -> str | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value.strip()

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_rss_feed(xml_text: str) -> list[NewsArticle]:
    root = ET.fromstring(xml_text)
    return [normalize_rss_item(item) for item in root.findall("./channel/item") if item.findtext("link")]


def fetch_google_news(keyword: str, lookback_days: int = 7, limit: int = 10) -> list[NewsArticle]:
    url = build_google_news_rss_url(keyword, lookback_days)
    request = Request(url, headers={"User-Agent": "contextnews-ai/0.1"})
    with urlopen(request, timeout=10) as response:
        xml_text = response.read().decode("utf-8")
    return parse_rss_feed(xml_text)[:limit]


def sample_news(keyword: str, lookback_days: int = 7, limit: int = 10) -> list[NewsArticle]:
    published_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    articles = [
        NewsArticle(
            title=f"{keyword} 관련 정책 변화와 시장 반응",
            url="https://example.com/contextnews/sample-policy",
            source="Sample News",
            description=f"{keyword}의 최근 흐름과 추가 쟁점을 정리한 샘플 기사입니다.",
            published_at=published_at,
        ),
        NewsArticle(
            title="관계없는 일반 경제 뉴스",
            url="https://example.com/contextnews/sample-economy",
            source="Sample News",
            description=f"최근 {lookback_days}일 동안의 거시 경제 동향을 다룹니다.",
            published_at=published_at,
        ),
    ]
    return articles[:limit]


def fetch_news(provider: str, keyword: str, lookback_days: int = 7, limit: int = 10) -> list[NewsArticle]:
    if provider == "sample":
        return sample_news(keyword, lookback_days, limit)
    if provider == "google_news_rss":
        return fetch_google_news(keyword, lookback_days, limit)
    raise ValueError(f"Unsupported news provider: {provider}")
