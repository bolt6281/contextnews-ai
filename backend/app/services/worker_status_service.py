from datetime import datetime, timezone

from app.config import get_settings
from app.database import db_session


def mark_stale_workers_offline() -> int:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    stale_ids: list[int] = []

    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, last_seen_at FROM ai_workers WHERE status != 'offline'",
        ).fetchall()
        for row in rows:
            last_seen_at = _parse_datetime(row["last_seen_at"])
            if (now - last_seen_at).total_seconds() >= settings.ai_worker_offline_after_seconds:
                stale_ids.append(row["id"])

        for worker_id in stale_ids:
            conn.execute(
                """
                UPDATE ai_workers
                SET status = 'offline',
                    current_job_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (worker_id,),
            )

    return len(stale_ids)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
