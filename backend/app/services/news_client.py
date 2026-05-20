from __future__ import annotations

import html
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

import httpx

from app.services.sample_data import sample_news

try:
    from app.config import get_settings
except ModuleNotFoundError:
    @dataclass(frozen=True)
    class _FallbackSettings:
        news_provider: str = os.getenv("NEWS_PROVIDER", "google_news_rss")
        news_fetch_limit: int = int(os.getenv("NEWS_FETCH_LIMIT", "10"))
        naver_client_id: str = os.getenv("NAVER_CLIENT_ID", "")
        naver_client_secret: str = os.getenv("NAVER_CLIENT_SECRET", "")

    def get_settings() -> _FallbackSettings:
        return _FallbackSettings()


GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
NAVER_NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = TAG_RE.sub(" ", value)
    unescaped = html.unescape(without_tags)
    return SPACE_RE.sub(" ", unescaped).strip()


def _normalize_published_at(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value.strip()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _build_google_news_url(keyword: str, lookback_days: int) -> str:
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


def _parse_google_item(item: ET.Element) -> dict[str, str]:
    source = item.find("source")
    article = {
        "title": _clean_text(item.findtext("title")),
        "url": (item.findtext("link") or "").strip(),
        "source": _clean_text(source.text if source is not None else ""),
        "description": _clean_text(item.findtext("description")),
        "published_at": _normalize_published_at(item.findtext("pubDate")),
    }
    return {**article, "raw_payload": json.dumps(article, ensure_ascii=False)}


def _parse_google_rss(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    return [_parse_google_item(item) for item in root.findall("./channel/item") if item.findtext("link")]


def _parse_naver_item(item: dict) -> dict[str, str]:
    article = {
        "title": _clean_text(item.get("title")),
        "url": item.get("originallink") or item.get("link") or "",
        "source": "Naver News",
        "description": _clean_text(item.get("description")),
        "published_at": _normalize_published_at(item.get("pubDate")),
    }
    return {**article, "raw_payload": json.dumps(item, ensure_ascii=False)}


async def _fetch_google_news(keyword: str, limit: int, lookback_days: int) -> list[dict[str, str]]:
    url = _build_google_news_url(keyword, lookback_days)
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "contextnews-ai/0.1"})
        response.raise_for_status()
    return _parse_google_rss(response.text)[:limit]


async def _fetch_naver_news(keyword: str, limit: int) -> list[dict[str, str]]:
    settings = get_settings()
    if not settings.naver_client_id or not settings.naver_client_secret:
        raise ValueError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are required for naver provider")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            NAVER_NEWS_URL,
            params={"query": keyword, "display": limit, "sort": "date"},
            headers={
                "X-Naver-Client-Id": settings.naver_client_id,
                "X-Naver-Client-Secret": settings.naver_client_secret,
            },
        )
        response.raise_for_status()
    return [_parse_naver_item(item) for item in response.json().get("items", [])]


async def fetch_news(
    keyword: str,
    limit: int | None = None,
    lookback_days: int = 7,
    provider: str | None = None,
) -> list[dict[str, str]]:
    settings = get_settings()
    selected_provider = provider or settings.news_provider
    fetch_limit = limit or settings.news_fetch_limit

    if selected_provider == "sample":
        return sample_news()[:fetch_limit]
    if selected_provider == "google_news_rss":
        return await _fetch_google_news(keyword, fetch_limit, lookback_days)
    if selected_provider == "naver":
        return await _fetch_naver_news(keyword, fetch_limit)
    raise ValueError(f"Unsupported news provider: {selected_provider}")
