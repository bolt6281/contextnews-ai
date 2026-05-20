from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..database import get_connection
from ..main import get_current_user
from ..schemas import InterestCreate, InterestResponse
from ..services.mock_ai_adapter import MockAIAdapter


router = APIRouter(prefix="/api/interests", tags=["interests"])
adapter = MockAIAdapter()


def serialize_interest(row: sqlite3.Row) -> InterestResponse:
    return InterestResponse(
        id=row["id"],
        keyword=row["keyword"],
        description=row["description"],
        lookback_days=row["lookback_days"],
        created_at=row["created_at"],
    )


@router.post("", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
def create_interest(payload: InterestCreate, current_user: sqlite3.Row = Depends(get_current_user)) -> InterestResponse:
    keyword_result = adapter.generate_hidden_keywords(payload.keyword, payload.description)

    with get_connection() as db:
        cursor = db.execute(
            """
            INSERT INTO interests (user_id, keyword, description, lookback_days)
            VALUES (?, ?, ?, ?)
            """,
            (current_user["id"], payload.keyword, payload.description, payload.lookback_days),
        )
        interest_id = cursor.lastrowid

        for hidden_keyword in keyword_result["hidden_keywords"]:
            db.execute(
                "INSERT INTO hidden_keywords (interest_id, keyword) VALUES (?, ?)",
                (interest_id, hidden_keyword),
            )

        db.execute(
            "INSERT INTO ai_jobs (job_type, payload) VALUES (?, ?)",
            (
                "hidden_keywords",
                json.dumps(
                    {
                        "user_id": current_user["id"],
                        "interest_id": interest_id,
                        "keyword": payload.keyword,
                        "description": payload.description,
                        "hidden_keywords": keyword_result["hidden_keywords"],
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        row = db.execute("SELECT * FROM interests WHERE id = ?", (interest_id,)).fetchone()

    return serialize_interest(row)


@router.get("", response_model=list[InterestResponse])
def list_interests(current_user: sqlite3.Row = Depends(get_current_user)) -> list[InterestResponse]:
    with get_connection() as db:
        rows = db.execute(
            "SELECT * FROM interests WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (current_user["id"],),
        ).fetchall()

    return [serialize_interest(row) for row in rows]


@router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interest(
    interest_id: int,
    current_user: sqlite3.Row = Depends(get_current_user),
) -> Response:
    with get_connection() as db:
        row = db.execute(
            "SELECT id FROM interests WHERE id = ? AND user_id = ?",
            (interest_id, current_user["id"]),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interest not found")

        pending_jobs = db.execute("SELECT id, payload FROM ai_jobs WHERE status = 'pending'").fetchall()
        for job in pending_jobs:
            try:
                job_payload = json.loads(job["payload"])
            except json.JSONDecodeError:
                continue
            if job_payload.get("interest_id") == interest_id:
                db.execute("DELETE FROM ai_jobs WHERE id = ?", (job["id"],))

        db.execute("DELETE FROM interests WHERE id = ?", (interest_id,))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
