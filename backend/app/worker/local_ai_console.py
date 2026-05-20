import argparse
import time

import httpx

from app.config import get_settings
from app.services.ai_job_service import process_job_with_codex


def process_pending_jobs(client: httpx.Client, base_url: str, headers: dict[str, str], worker_id: str, limit: int) -> int:
    claim = client.post(
        f"{base_url}/api/internal/ai-jobs/claim",
        headers=headers,
        json={"worker_id": worker_id, "limit": limit},
    )
    claim.raise_for_status()
    jobs = claim.json()["jobs"]

    for job in jobs:
        try:
            result = process_job_with_codex(job)
            complete = client.post(
                f"{base_url}/api/internal/ai-jobs/{job['id']}/complete",
                headers=headers,
                json={"worker_id": worker_id, "result": result},
            )
            complete.raise_for_status()
            print(f"completed job #{job['id']} ({job['job_type']})")
        except Exception as exc:
            client.post(
                f"{base_url}/api/internal/ai-jobs/{job['id']}/fail",
                headers=headers,
                json={"worker_id": worker_id, "error_message": str(exc)},
            )
            print(f"failed job #{job['id']}: {exc}")

    return len(jobs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local AI console worker")
    parser.add_argument("--drain", action="store_true", help="process pending jobs and exit")
    args = parser.parse_args()

    settings = get_settings()
    base_url = "http://localhost:8000"
    headers = {"X-AI-Worker-Token": settings.ai_worker_token}
    print(f"Local AI console started: worker_id={settings.ai_worker_id}")
    with httpx.Client(timeout=20) as client:
        while True:
            heartbeat = client.post(
                f"{base_url}/api/internal/ai-workers/heartbeat",
                headers=headers,
                json={"worker_id": settings.ai_worker_id, "status": "online"},
            )
            heartbeat.raise_for_status()

            processed = process_pending_jobs(
                client,
                base_url,
                headers,
                settings.ai_worker_id,
                settings.ai_candidate_limit,
            )

            if args.drain and processed == 0:
                return
            if processed == 0:
                time.sleep(settings.ai_worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
