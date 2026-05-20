from __future__ import annotations

import json
from datetime import UTC, datetime


def sample_news() -> list[dict[str, str]]:
    published_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    articles = [
        {
            "title": "AI 반도체 공급망 재편",
            "url": "https://example.com/contextnews/ai-semiconductor",
            "source": "Sample News",
            "description": "AI 칩과 메모리 수요가 늘며 반도체 공급망이 재편되고 있습니다.",
            "published_at": published_at,
        },
        {
            "title": "데이터센터 전력 인프라 투자 확대",
            "url": "https://example.com/contextnews/datacenter-power",
            "source": "Sample News",
            "description": "데이터센터 증가로 전력 인프라와 냉각 기술 투자가 확대되고 있습니다.",
            "published_at": published_at,
        },
        {
            "title": "생성형 AI 서비스 경쟁 심화",
            "url": "https://example.com/contextnews/generative-ai",
            "source": "Sample News",
            "description": "주요 기업들이 생성형 AI 서비스 고도화와 수익화 전략을 강화하고 있습니다.",
            "published_at": published_at,
        },
    ]
    return [{**article, "raw_payload": json.dumps(article, ensure_ascii=False)} for article in articles]
