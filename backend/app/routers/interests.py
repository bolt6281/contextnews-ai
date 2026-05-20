from fastapi import APIRouter, Depends, HTTPException, status

from app.database import db_session
from app.dependencies import get_current_user
from app.schemas import InterestCreateRequest, InterestResponse
from app.services.ai_job_service import create_ai_job

router = APIRouter(prefix="/api/interests", tags=["interests"])


@router.get("")
def list_interests(user: dict = Depends(get_current_user)):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT id, keyword, description, lookback_days, created_at
            FROM interests
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        return {"interests": [dict(row) for row in rows]}


@router.post("", response_model=InterestResponse)
def create_interest(payload: InterestCreateRequest, user: dict = Depends(get_current_user)):
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO interests (user_id, keyword, description, lookback_days) VALUES (?, ?, ?, ?)",
            (user["id"], payload.keyword, payload.description, payload.lookback_days),
        )
        interest_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, keyword, description, lookback_days, created_at FROM interests WHERE id = ?",
            (interest_id,),
        ).fetchone()

    ai_job_id = create_ai_job(
        user["id"],
        "hidden_keywords",
        {
            "interest_id": interest_id,
            "keyword": payload.keyword,
            "description": payload.description,
            "lookback_days": payload.lookback_days,
        },
    )
    return InterestResponse(**dict(row), ai_job_id=ai_job_id, ai_job_status="pending")


@router.delete("/{interest_id}")
def delete_interest(interest_id: int, user: dict = Depends(get_current_user)):
    with db_session() as conn:
        row = conn.execute(
            "SELECT id FROM interests WHERE id = ? AND user_id = ?",
            (interest_id, user["id"]),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관심 키워드를 찾을 수 없습니다.")

        conn.execute(
            """
            DELETE FROM ai_jobs
            WHERE user_id = ?
              AND status = 'pending'
              AND (
                json_extract(payload, '$.interest_id') = ?
                OR json_extract(payload, '$.interest.id') = ?
              )
            """,
            (user["id"], interest_id, interest_id),
        )
        conn.execute("DELETE FROM interests WHERE id = ? AND user_id = ?", (interest_id, user["id"]))

    return {"ok": True, "interest_id": interest_id}
