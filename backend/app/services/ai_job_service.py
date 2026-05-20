import json
from datetime import datetime, timezone

from app.database import db_session
from app.services.codex_cli_adapter import decide_article as codex_decide_article
from app.services.codex_cli_adapter import generate_hidden_keywords as codex_generate_hidden_keywords
from app.services.mock_ai_adapter import decide_article, generate_hidden_keywords


def create_ai_job(user_id: int, job_type: str, payload: dict) -> int:
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO ai_jobs (user_id, job_type, status, payload) VALUES (?, ?, 'pending', ?)",
            (user_id, job_type, json.dumps(payload, ensure_ascii=False)),
        )
        return cur.lastrowid


def claim_jobs(worker_id: str, limit: int) -> list[dict]:
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT * FROM ai_jobs
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        jobs = []
        for row in rows:
            conn.execute(
                "UPDATE ai_jobs SET status = 'processing', locked_by = ?, locked_at = CURRENT_TIMESTAMP WHERE id = ?",
                (worker_id, row["id"]),
            )
            jobs.append({"id": row["id"], "job_type": row["job_type"], "payload": json.loads(row["payload"])})
        return jobs


def complete_job(job_id: int, worker_id: str, result: dict) -> None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM ai_jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("AI 작업을 찾을 수 없습니다.")
        if row["locked_by"] not in (None, worker_id):
            raise ValueError("다른 worker가 점유한 작업입니다.")

        payload = json.loads(row["payload"])
        if row["job_type"] == "hidden_keywords":
            for keyword in result.get("hidden_keywords", []):
                conn.execute(
                    "INSERT OR IGNORE INTO hidden_keywords (interest_id, keyword) VALUES (?, ?)",
                    (payload["interest_id"], keyword),
                )
        elif row["job_type"] == "article_decision":
            candidate_id = payload["candidate_article_id"]
            conn.execute(
                """
                INSERT INTO ai_decisions
                  (candidate_article_id, accepted, reason, summary, bullet_points, ai_mode)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    1 if result.get("accepted") else 0,
                    result.get("reason", ""),
                    result.get("summary", ""),
                    json.dumps(result.get("bullet_points", []), ensure_ascii=False),
                    result.get("ai_mode", "mock"),
                ),
            )

        conn.execute(
            """
            UPDATE ai_jobs
            SET status = 'completed', result = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (json.dumps(result, ensure_ascii=False), job_id),
        )
        conn.execute(
            """
            UPDATE ai_workers
            SET processed_count = processed_count + 1,
                current_job_id = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE worker_id = ?
            """,
            (worker_id,),
        )


def fail_job(job_id: int, worker_id: str, error_message: str) -> None:
    with db_session() as conn:
        conn.execute(
            """
            UPDATE ai_jobs
            SET status = 'failed', error_message = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND (locked_by IS NULL OR locked_by = ?)
            """,
            (error_message, job_id, worker_id),
        )


def heartbeat(worker_id: str, status: str = "online") -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO ai_workers (worker_id, status, last_seen_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(worker_id) DO UPDATE SET
              status = excluded.status,
              last_seen_at = excluded.last_seen_at,
              updated_at = CURRENT_TIMESTAMP
            """,
            (worker_id, status, now),
        )
        pending = conn.execute("SELECT COUNT(*) AS count FROM ai_jobs WHERE status = 'pending'").fetchone()["count"]
        return {"worker_id": worker_id, "status": status, "pending_ai_jobs": pending, "server_time": now}


def process_job_with_mock(job: dict) -> dict:
    payload = job["payload"]
    if job["job_type"] == "hidden_keywords":
        return {
            "hidden_keywords": generate_hidden_keywords(payload["keyword"], payload["description"]),
            "ai_mode": "mock",
        }
    if job["job_type"] == "article_decision":
        result = decide_article(payload["interest"], payload["article"], payload["matched_keywords"])
        result["ai_mode"] = "mock"
        return result
    raise ValueError(f"Unsupported job type: {job['job_type']}")


def process_job_with_codex(job: dict) -> dict:
    payload = job["payload"]
    if job["job_type"] == "hidden_keywords":
        return codex_generate_hidden_keywords(payload["keyword"], payload["description"])
    if job["job_type"] == "article_decision":
        return codex_decide_article(payload["interest"], payload["article"], payload["matched_keywords"])
    raise ValueError(f"Unsupported job type: {job['job_type']}")
