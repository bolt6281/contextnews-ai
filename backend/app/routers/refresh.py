import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.config import get_settings
from app.database import db_session
from app.dependencies import get_current_user
from app.schemas import RefreshRequest
from app.services.ai_job_service import create_ai_job
from app.services.candidate_filter import find_matched_keywords
from app.services.news_client import fetch_news

router = APIRouter(prefix="/api/refresh", tags=["refresh"])


@router.post("")
async def refresh(payload: RefreshRequest, user: dict = Depends(get_current_user)):
    settings = get_settings()
    fetched_articles = 0
    candidate_articles = 0
    created_ai_jobs = 0

    with db_session() as conn:
        interests = conn.execute(
            "SELECT * FROM interests WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()

    for interest_row in interests:
        interest = dict(interest_row)
        with db_session() as conn:
            hidden_rows = conn.execute(
                "SELECT keyword FROM hidden_keywords WHERE interest_id = ? ORDER BY id ASC",
                (interest["id"],),
            ).fetchall()
        hidden_keywords = [row["keyword"] for row in hidden_rows]
        if not hidden_keywords:
            continue

        search_query = _build_news_search_query(interest, hidden_keywords)
        articles = await fetch_news(
            search_query,
            min(payload.limit_per_interest, settings.news_fetch_limit),
            interest["lookback_days"],
        )
        articles = [article for article in articles if _within_lookback(article["published_at"], interest["lookback_days"])]
        fetched_articles += len(articles)

        for article in articles:
            with db_session() as conn:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO articles
                      (title, source, url, description, published_at, raw_payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article["title"],
                        article["source"],
                        article["url"],
                        article["description"],
                        article["published_at"],
                        article.get("raw_payload", "{}"),
                    ),
                )
                article_row = conn.execute("SELECT * FROM articles WHERE url = ?", (article["url"],)).fetchone()

            matched = find_matched_keywords(article["title"], article["description"], hidden_keywords)
            if not matched:
                continue

            with db_session() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO candidate_articles
                      (interest_id, article_id, matched_keywords)
                    VALUES (?, ?, ?)
                    """,
                    (interest["id"], article_row["id"], json.dumps(matched, ensure_ascii=False)),
                )
                candidate_row = conn.execute(
                    """
                    SELECT * FROM candidate_articles
                    WHERE interest_id = ? AND article_id = ?
                    """,
                    (interest["id"], article_row["id"]),
                ).fetchone()
                existing_decision = conn.execute(
                    "SELECT id FROM ai_decisions WHERE candidate_article_id = ?",
                    (candidate_row["id"],),
                ).fetchone()
                existing_job = conn.execute(
                    """
                    SELECT id FROM ai_jobs
                    WHERE job_type = 'article_decision'
                      AND json_extract(payload, '$.candidate_article_id') = ?
                      AND status IN ('pending', 'processing', 'completed')
                    """,
                    (candidate_row["id"],),
                ).fetchone()

            candidate_articles += 1
            if existing_decision or existing_job:
                continue

            create_ai_job(
                user["id"],
                "article_decision",
                {
                    "candidate_article_id": candidate_row["id"],
                    "interest": {
                        "id": interest["id"],
                        "keyword": interest["keyword"],
                        "description": interest["description"],
                        "lookback_days": interest["lookback_days"],
                    },
                    "article": dict(article_row),
                    "matched_keywords": matched,
                },
            )
            created_ai_jobs += 1

    with db_session() as conn:
        pending_ai_jobs = conn.execute(
            "SELECT COUNT(*) AS count FROM ai_jobs WHERE user_id = ? AND status = 'pending'",
            (user["id"],),
        ).fetchone()["count"]

    return {
        "fetched_articles": fetched_articles,
        "candidate_articles": candidate_articles,
        "created_ai_jobs": created_ai_jobs,
        "pending_ai_jobs": pending_ai_jobs,
    }


def _within_lookback(published_at: str, lookback_days: int) -> bool:
    try:
        parsed = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    return parsed.astimezone(timezone.utc) >= cutoff


def _build_news_search_query(interest: dict, hidden_keywords: list[str]) -> str:
    keyword = str(interest["keyword"]).strip()
    for hidden_keyword in hidden_keywords:
        hidden = str(hidden_keyword).strip()
        if not hidden:
            continue
        if keyword and keyword.casefold() in hidden.casefold():
            return hidden
        if keyword:
            return f"{keyword} {hidden}"
        return hidden
    return keyword
