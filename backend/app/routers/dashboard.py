from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_connection
from ..main import get_current_user
from ..schemas import DashboardResponse


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def serialize_article(row: sqlite3.Row) -> dict:
    scrapped_at = row["scrapped_at"]
    return {
        "candidate_article_id": row["candidate_article_id"],
        "interest_id": row["interest_id"],
        "article_id": row["article_id"],
        "title": row["title"],
        "url": row["url"],
        "source": row["source"],
        "description": row["description"],
        "published_at": row["published_at"],
        "summary": row["summary"],
        "bullet_points": parse_json_list(row["bullet_points"]),
        "matched_keywords": parse_json_list(row["matched_keywords"]),
        "is_read": row["read_at"] is not None,
        "read_at": row["read_at"],
        "is_scrapped": scrapped_at is not None,
        "scrapped_at": scrapped_at,
    }


def dashboard_articles(db: sqlite3.Connection, user_id: int, scrapped_only: bool = False) -> list[dict]:
    where_scrap = "AND scraps.id IS NOT NULL" if scrapped_only else ""
    rows = db.execute(
        f"""
        SELECT
            candidate_articles.id AS candidate_article_id,
            candidate_articles.interest_id,
            candidate_articles.matched_keywords,
            articles.id AS article_id,
            articles.title,
            articles.url,
            articles.source,
            articles.description,
            articles.published_at,
            ai_decisions.summary,
            ai_decisions.bullet_points,
            article_reads.read_at,
            scraps.created_at AS scrapped_at
        FROM candidate_articles
        JOIN interests ON interests.id = candidate_articles.interest_id
        JOIN articles ON articles.id = candidate_articles.article_id
        JOIN ai_decisions ON ai_decisions.candidate_article_id = candidate_articles.id
        LEFT JOIN article_reads
            ON article_reads.article_id = articles.id AND article_reads.user_id = interests.user_id
        LEFT JOIN scraps
            ON scraps.candidate_article_id = candidate_articles.id AND scraps.user_id = interests.user_id
        WHERE interests.user_id = ? AND ai_decisions.accepted = 1
        {where_scrap}
        ORDER BY COALESCE(articles.published_at, articles.created_at) DESC, candidate_articles.id DESC
        """,
        (user_id,),
    ).fetchall()
    return [serialize_article(row) for row in rows]


@router.get("", response_model=DashboardResponse)
def dashboard(current_user: sqlite3.Row = Depends(get_current_user)) -> DashboardResponse:
    with get_connection() as db:
        interests = [
            dict(row)
            for row in db.execute(
                "SELECT id, keyword, description, lookback_days, created_at FROM interests WHERE user_id = ? ORDER BY id",
                (current_user["id"],),
            ).fetchall()
        ]
        workers = [
            dict(row)
            for row in db.execute(
                "SELECT worker_name, last_seen_at, processed_count, status FROM ai_workers ORDER BY worker_name"
            ).fetchall()
        ]
        pending_count = db.execute("SELECT COUNT(*) AS count FROM ai_jobs WHERE status = 'pending'").fetchone()["count"]
        articles = dashboard_articles(db, current_user["id"])
        scrapped_articles = dashboard_articles(db, current_user["id"], scrapped_only=True)

    return DashboardResponse(
        interests=interests,
        articles=articles,
        pending_ai_jobs=pending_count,
        ai_workers=workers,
        scrapped_articles=scrapped_articles,
    )


@router.post("/articles/{article_id}/read", status_code=status.HTTP_201_CREATED)
def mark_read(article_id: int, current_user: sqlite3.Row = Depends(get_current_user)) -> dict[str, str]:
    with get_connection() as db:
        article = db.execute("SELECT id FROM articles WHERE id = ?", (article_id,)).fetchone()
        if article is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

        db.execute(
            """
            INSERT INTO article_reads (user_id, article_id)
            VALUES (?, ?)
            ON CONFLICT(user_id, article_id) DO UPDATE SET read_at = CURRENT_TIMESTAMP
            """,
            (current_user["id"], article_id),
        )

    return {"status": "ok"}
