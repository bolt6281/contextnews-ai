from datetime import datetime, timedelta, timezone


def sample_news(keyword: str) -> list[dict]:
    # 네트워크 없이도 뉴스 수집과 대시보드 흐름을 확인할 수 있는 고정 샘플 데이터다.
    now = datetime.now(timezone.utc)
    return [
        {
            "title": f"{keyword}, 실적 전망 개선에 시장 관심 집중",
            "source": "Sample Business",
            "url": f"https://example.com/news/{keyword}-earnings",
            "description": f"{keyword} 관련 실적, 주가, 투자 전망을 다룬 기사입니다.",
            "published_at": (now - timedelta(hours=1)).isoformat(),
            "raw_payload": "{}",
        },
        {
            "title": f"{keyword} 기술 발표와 산업 변화 분석",
            "source": "Sample Tech",
            "url": f"https://example.com/news/{keyword}-tech",
            "description": f"{keyword} 기술, 제품, 시장 흐름을 설명하는 기사입니다.",
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "raw_payload": "{}",
        },
        {
            "title": "환율과 금리 변화가 증시에 미친 영향",
            "source": "Sample Economy",
            "url": "https://example.com/news/market-macro",
            "description": "거시경제와 금융시장 전반을 다룬 기사입니다.",
            "published_at": (now - timedelta(hours=3)).isoformat(),
            "raw_payload": "{}",
        },
    ]
