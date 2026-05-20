import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import db_session
from app.dependencies import get_current_user
from app.services.worker_status_service import mark_stale_workers_offline

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(user: dict = Depends(get_current_user)):
    mark_stale_workers_offline()
    with db_session() as conn:
        interests = conn.execute(
            """
            SELECT id, keyword, description, lookback_days, created_at
            FROM interests
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        pending = conn.execute(
            "SELECT COUNT(*) AS count FROM ai_jobs WHERE user_id = ? AND status IN ('pending', 'processing')",
            (user["id"],),
        ).fetchone()["count"]
        candidates = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM candidate_articles
            JOIN interests ON interests.id = candidate_articles.interest_id
            WHERE interests.user_id = ?
            """,
            (user["id"],),
        ).fetchone()["count"]
        scraps = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM article_scraps
            JOIN candidate_articles ON candidate_articles.id = article_scraps.candidate_article_id
            JOIN interests ON interests.id = candidate_articles.interest_id
            WHERE article_scraps.user_id = ? AND interests.user_id = ?
            """,
            (user["id"], user["id"]),
        ).fetchone()["count"]
        items = conn.execute(
            """
            SELECT
              candidate_articles.id AS candidate_article_id,
              articles.id AS article_id,
              interests.id AS interest_id,
              articles.title,
              articles.source,
              articles.url,
              articles.description,
              articles.published_at,
              interests.keyword,
              ai_decisions.summary,
              ai_decisions.bullet_points,
              ai_decisions.reason AS decision_reason,
              ai_decisions.created_at AS decided_at,
              article_scraps.created_at AS scrapped_at,
              article_reads.read_at
            FROM ai_decisions
            JOIN candidate_articles ON candidate_articles.id = ai_decisions.candidate_article_id
            JOIN articles ON articles.id = candidate_articles.article_id
            JOIN interests ON interests.id = candidate_articles.interest_id
            LEFT JOIN article_scraps
              ON article_scraps.candidate_article_id = candidate_articles.id
             AND article_scraps.user_id = interests.user_id
            LEFT JOIN article_reads
              ON article_reads.article_id = articles.id
             AND article_reads.user_id = interests.user_id
            WHERE interests.user_id = ? AND ai_decisions.accepted = 1
            ORDER BY articles.published_at DESC
            """,
            (user["id"],),
        ).fetchall()
        worker = conn.execute(
            "SELECT worker_id, status, last_seen_at, processed_count FROM ai_workers ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()

    parsed_items = []
    for row in items:
        item = dict(row)
        item["bullet_points"] = json.loads(item["bullet_points"] or "[]")
        item["is_read"] = item["read_at"] is not None
        item["is_scrapped"] = item["scrapped_at"] is not None
        parsed_items.append(item)

    return {
        "user": {"id": user["id"], "email": user["email"], "display_name": user["display_name"]},
        "interests": [dict(row) for row in interests],
            "stats": {
                "interest_count": len(interests),
                "candidate_articles": candidates,
                "pending_ai_jobs": pending,
                "accepted_articles": len(parsed_items),
                "scrapped_articles": scraps,
            },
        "worker": dict(worker) if worker else {"status": "offline"},
        "items": parsed_items,
    }


@router.post("/articles/{article_id}/read")
def mark_article_read(article_id: int, user: dict = Depends(get_current_user)):
    with db_session() as conn:
        article = conn.execute(
            """
            SELECT articles.id
            FROM articles
            JOIN candidate_articles ON candidate_articles.article_id = articles.id
            JOIN ai_decisions ON ai_decisions.candidate_article_id = candidate_articles.id
            JOIN interests ON interests.id = candidate_articles.interest_id
            WHERE articles.id = ?
              AND interests.user_id = ?
              AND ai_decisions.accepted = 1
            LIMIT 1
            """,
            (article_id, user["id"]),
        ).fetchone()
        if article is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="열람 가능한 뉴스를 찾지 못했습니다.")

        conn.execute(
            "INSERT OR IGNORE INTO article_reads (user_id, article_id) VALUES (?, ?)",
            (user["id"], article_id),
        )
        read = conn.execute(
            "SELECT read_at FROM article_reads WHERE user_id = ? AND article_id = ?",
            (user["id"], article_id),
        ).fetchone()

    return {"article_id": article_id, "is_read": True, "read_at": read["read_at"]}
