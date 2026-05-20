from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_connection
from ..main import get_current_user
from ..schemas import RefreshRequest, RefreshResponse
from ..services.candidate_filter import filter_candidates


router = APIRouter(prefix="/api/refresh", tags=["refresh"])


def hidden_keywords_for(db: sqlite3.Connection, interest_id: int) -> list[str]:
    rows = db.execute(
        "SELECT keyword FROM hidden_keywords WHERE interest_id = ? ORDER BY id",
        (interest_id,),
    ).fetchall()
    return [row["keyword"] for row in rows]


@router.post("", response_model=RefreshResponse)
def refresh(payload: RefreshRequest, current_user: sqlite3.Row = Depends(get_current_user)) -> RefreshResponse:
    with get_connection() as db:
        if payload.interest_id is None:
            interests = db.execute(
                "SELECT * FROM interests WHERE user_id = ? ORDER BY id",
                (current_user["id"],),
            ).fetchall()
        else:
            interests = db.execute(
                "SELECT * FROM interests WHERE id = ? AND user_id = ?",
                (payload.interest_id, current_user["id"]),
            ).fetchall()
            if not interests:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interest not found")

        response_jobs = []
        input_articles = [article.model_dump(mode="json") for article in payload.articles]

        for interest in interests:
            search_terms = hidden_keywords_for(db, interest["id"]) or [interest["keyword"]]
            candidates = filter_candidates(input_articles, search_terms) if input_articles else []

            refresh_cursor = db.execute(
                "INSERT INTO ai_jobs (job_type, payload) VALUES (?, ?)",
                (
                    "news_refresh",
                    json.dumps(
                        {
                            "user_id": current_user["id"],
                            "interest_id": interest["id"],
                            "search_terms": search_terms,
                            "lookback_days": interest["lookback_days"],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )

            for candidate in candidates:
                article = candidate["article"]
                db.execute(
                    """
                    INSERT INTO articles (title, url, source, description, published_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        title = excluded.title,
                        source = excluded.source,
                        description = excluded.description,
                        published_at = excluded.published_at
                    """,
                    (
                        article["title"],
                        article["url"],
                        article.get("source"),
                        article.get("description"),
                        article.get("published_at"),
                    ),
                )
                article_row = db.execute("SELECT id FROM articles WHERE url = ?", (article["url"],)).fetchone()
                db.execute(
                    """
                    INSERT OR IGNORE INTO candidate_articles (interest_id, article_id, matched_keywords)
                    VALUES (?, ?, ?)
                    """,
                    (interest["id"], article_row["id"], json.dumps(candidate["matched_keywords"], ensure_ascii=False)),
                )
                candidate_row = db.execute(
                    "SELECT id FROM candidate_articles WHERE interest_id = ? AND article_id = ?",
                    (interest["id"], article_row["id"]),
                ).fetchone()
                db.execute(
                    "INSERT INTO ai_jobs (job_type, payload) VALUES (?, ?)",
                    (
                        "article_decision",
                        json.dumps(
                            {
                                "user_id": current_user["id"],
                                "interest_id": interest["id"],
                                "candidate_article_id": candidate_row["id"],
                                "matched_keywords": candidate["matched_keywords"],
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )

            response_jobs.append(
                {
                    "id": refresh_cursor.lastrowid,
                    "interest_id": interest["id"],
                    "search_terms": search_terms,
                    "candidate_count": len(candidates),
                }
            )

        pending_count = db.execute("SELECT COUNT(*) AS count FROM ai_jobs WHERE status = 'pending'").fetchone()["count"]

    return RefreshResponse(status="queued", pending_ai_jobs=pending_count, jobs=response_jobs)
