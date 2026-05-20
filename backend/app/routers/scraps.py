from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..database import get_connection
from ..main import get_current_user
from ..routers.dashboard import dashboard_articles
from ..schemas import ScrapCreate


router = APIRouter(prefix="/api/scraps", tags=["scraps"])


def ensure_candidate_for_user(db: sqlite3.Connection, candidate_article_id: int, user_id: int) -> None:
    row = db.execute(
        """
        SELECT candidate_articles.id
        FROM candidate_articles
        JOIN interests ON interests.id = candidate_articles.interest_id
        WHERE candidate_articles.id = ? AND interests.user_id = ?
        """,
        (candidate_article_id, user_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate article not found")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_scrap(payload: ScrapCreate, current_user: sqlite3.Row = Depends(get_current_user)) -> dict:
    with get_connection() as db:
        ensure_candidate_for_user(db, payload.candidate_article_id, current_user["id"])
        db.execute(
            "INSERT OR IGNORE INTO scraps (user_id, candidate_article_id) VALUES (?, ?)",
            (current_user["id"], payload.candidate_article_id),
        )
        articles = [
            article
            for article in dashboard_articles(db, current_user["id"], scrapped_only=True)
            if article["candidate_article_id"] == payload.candidate_article_id
        ]

    return articles[0] if articles else {"candidate_article_id": payload.candidate_article_id}


@router.get("")
def list_scraps(current_user: sqlite3.Row = Depends(get_current_user)) -> list[dict]:
    with get_connection() as db:
        return dashboard_articles(db, current_user["id"], scrapped_only=True)


@router.delete("/{candidate_article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scrap(
    candidate_article_id: int,
    current_user: sqlite3.Row = Depends(get_current_user),
) -> Response:
    with get_connection() as db:
        ensure_candidate_for_user(db, candidate_article_id, current_user["id"])
        db.execute(
            "DELETE FROM scraps WHERE user_id = ? AND candidate_article_id = ?",
            (current_user["id"], candidate_article_id),
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
