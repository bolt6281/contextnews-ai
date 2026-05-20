import importlib
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", str(tmp_path / "test.db"))
    from app import database
    from app import main

    importlib.reload(database)
    importlib.reload(main)
    main.init_db()
    return TestClient(main.app), database


def register(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123", "display_name": "User"},
    )
    assert response.status_code == 201
    return response.json()["token"]


def test_refresh_queues_jobs_with_description_keywords_and_candidates(tmp_path, monkeypatch):
    client, database = build_client(tmp_path, monkeypatch)
    token = register(client)
    interest = client.post(
        "/api/interests",
        headers={"Authorization": f"Bearer {token}"},
        json={"keyword": "AI", "description": "반도체 전력 인프라", "lookback_days": 30},
    ).json()

    response = client.post(
        "/api/refresh",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "interest_id": interest["id"],
            "articles": [
                {
                    "title": "데이터센터 전력 투자 확대",
                    "url": "https://example.com/power",
                    "source": "Example",
                    "description": "AI 인프라 수요가 늘었습니다.",
                },
                {
                    "title": "여행 수요 증가",
                    "url": "https://example.com/travel",
                    "description": "항공권 판매가 늘었습니다.",
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["jobs"][0]["candidate_count"] == 1
    assert {"AI", "반도체", "전력", "인프라"}.issubset(set(payload["jobs"][0]["search_terms"]))
    assert payload["pending_ai_jobs"] == 3

    with database.get_connection() as db:
        decision_job = db.execute("SELECT payload FROM ai_jobs WHERE job_type = 'article_decision'").fetchone()
    assert json.loads(decision_job["payload"])["matched_keywords"]
