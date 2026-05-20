import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import db_session
from app.dependencies import get_current_user
from app.schemas import ScrapCreateRequest

router = APIRouter(prefix="/api/scraps", tags=["scraps"])


@router.get("")
def list_scraps(user: dict = Depends(get_current_user)):
    return {"items": _scrap_items(user["id"])}


@router.post("")
def create_scrap(payload: ScrapCreateRequest, user: dict = Depends(get_current_user)):
    with db_session() as conn:
        candidate = conn.execute(
            """
            SELECT candidate_articles.id
            FROM candidate_articles
            JOIN interests ON interests.id = candidate_articles.interest_id
            JOIN ai_decisions ON ai_decisions.candidate_article_id = candidate_articles.id
            WHERE candidate_articles.id = ?
              AND interests.user_id = ?
              AND ai_decisions.accepted = 1
            LIMIT 1
            """,
            (payload.candidate_article_id, user["id"]),
        ).fetchone()
        if candidate is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="스크랩할 뉴스를 찾지 못했습니다.")

        conn.execute(
            """
            INSERT OR IGNORE INTO article_scraps (user_id, candidate_article_id)
            VALUES (?, ?)
            """,
            (user["id"], payload.candidate_article_id),
        )
        row = conn.execute(
            """
            SELECT created_at
            FROM article_scraps
            WHERE user_id = ? AND candidate_article_id = ?
            """,
            (user["id"], payload.candidate_article_id),
        ).fetchone()

    return {
        "ok": True,
        "candidate_article_id": payload.candidate_article_id,
        "scrapped_at": row["created_at"],
    }


@router.delete("/{candidate_article_id}")
def delete_scrap(candidate_article_id: int, user: dict = Depends(get_current_user)):
    with db_session() as conn:
        cur = conn.execute(
            "DELETE FROM article_scraps WHERE user_id = ? AND candidate_article_id = ?",
            (user["id"], candidate_article_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="스크랩한 뉴스를 찾지 못했습니다.")

    return {"ok": True, "candidate_article_id": candidate_article_id}


def _scrap_items(user_id: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
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
              article_reads.read_at,
              article_scraps.created_at AS scrapped_at
            FROM article_scraps
            JOIN candidate_articles ON candidate_articles.id = article_scraps.candidate_article_id
            JOIN articles ON articles.id = candidate_articles.article_id
            JOIN interests ON interests.id = candidate_articles.interest_id
            JOIN ai_decisions ON ai_decisions.candidate_article_id = candidate_articles.id
            LEFT JOIN article_reads
              ON article_reads.article_id = articles.id
             AND article_reads.user_id = article_scraps.user_id
            WHERE article_scraps.user_id = ?
              AND interests.user_id = ?
              AND ai_decisions.accepted = 1
            ORDER BY article_scraps.created_at DESC
            """,
            (user_id, user_id),
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        item["bullet_points"] = json.loads(item["bullet_points"] or "[]")
        item["is_read"] = item["read_at"] is not None
        item["is_scrapped"] = True
        items.append(item)
    return items
