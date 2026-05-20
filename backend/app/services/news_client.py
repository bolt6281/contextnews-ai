import html
import json
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.services.sample_data import sample_news


TAG_RE = re.compile(r"<[^>]+>")
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def _clean(value: str) -> str:
    # RSS title/description에 섞인 HTML 태그와 entity를 화면 표시용 문자열로 정리한다.
    return TAG_RE.sub("", html.unescape(value or "")).strip()


async def fetch_news(keyword: str, limit: int, lookback_days: int = 7) -> list[dict]:
    # refresh API가 호출하는 뉴스 수집 진입점이다. provider는 backend 설정값을 따른다.
    settings = get_settings()
    provider = settings.news_provider.lower()

    if provider == "sample":
        return sample_news(keyword)[:limit]

    if provider == "naver" and settings.naver_client_id and settings.naver_client_secret:
        return await _fetch_naver_news(keyword, limit)

    return await _fetch_google_news(keyword, limit, lookback_days)


async def _fetch_naver_news(keyword: str, limit: int) -> list[dict]:
    # Naver provider를 사용할 때도 Google RSS와 같은 article dict 구조로 정규화한다.
    settings = get_settings()
    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }
    params = {"query": keyword, "display": limit, "sort": "date"}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get("https://openapi.naver.com/v1/search/news.json", headers=headers, params=params)
        response.raise_for_status()
        payload = response.json()

    normalized: list[dict] = []
    for item in payload.get("items", []):
        published_at = parsedate_to_datetime(item["pubDate"]).isoformat()
        normalized.append(
            {
                "title": _clean(item.get("title", "")),
                "source": "Naver News",
                "url": item.get("originallink") or item.get("link"),
                "description": _clean(item.get("description", "")),
                "published_at": published_at,
                "raw_payload": json.dumps(item, ensure_ascii=False),
            }
        )
    return normalized


async def _fetch_google_news(keyword: str, limit: int, lookback_days: int) -> list[dict]:
    # Google News RSS는 API key 없이 keyword와 lookback 기간 조건으로 후보 뉴스를 가져온다.
    params = {
        "q": f"{keyword} when:{lookback_days}d",
        "hl": "ko",
        "gl": "KR",
        "ceid": "KR:ko",
    }
    url = f"{GOOGLE_NEWS_RSS_URL}?{urlencode(params)}"
    headers = {"User-Agent": "ContextNews/0.1"}

    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

    root = ET.fromstring(response.text)
    items = root.findall("./channel/item")
    normalized: list[dict] = []

    for item in items[:limit]:
        normalized_item = _parse_google_item(item)
        if normalized_item is not None:
            normalized.append(normalized_item)

    return normalized


def _parse_google_item(item: ET.Element) -> dict | None:
    # RSS item 하나를 backend가 저장하는 article 필드 구조로 변환한다.
    raw_title = _clean(item.findtext("title", default=""))
    link = item.findtext("link", default="").strip()
    pub_date = item.findtext("pubDate", default="").strip()
    source = _clean(item.findtext("source", default="Google News")) or "Google News"
    description = _clean(item.findtext("description", default=""))

    if not raw_title or not link or not pub_date:
        return None

    try:
        published_at = parsedate_to_datetime(pub_date).isoformat()
    except (TypeError, ValueError):
        return None

    title = _strip_source_suffix(raw_title, source)
    return {
        "title": title,
        "source": source,
        "url": link,
        "description": description or title,
        "published_at": published_at,
        "raw_payload": json.dumps(
            {
                "provider": "google_news",
                "title": raw_title,
                "source": source,
                "link": link,
                "pubDate": pub_date,
                "description": description,
            },
            ensure_ascii=False,
        ),
    }


def _strip_source_suffix(title: str, source: str) -> str:
    # Google RSS 제목 끝의 언론사 suffix는 source 필드와 중복되므로 제거한다.
    suffix = f" - {source}"
    if title.endswith(suffix):
        return title[: -len(suffix)].strip()
    return title
