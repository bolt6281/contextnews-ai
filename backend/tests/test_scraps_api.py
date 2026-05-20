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


def register(client, email):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": email.split("@")[0]},
    )
    assert response.status_code == 201
    return response.json()["token"]


def create_accepted_candidate(client, database, token):
    interest = client.post(
        "/api/interests",
        headers={"Authorization": f"Bearer {token}"},
        json={"keyword": "AI", "description": "전력", "lookback_days": 7},
    ).json()
    refresh = client.post(
        "/api/refresh",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "interest_id": interest["id"],
            "articles": [
                {
                    "title": "AI 전력 수요 증가",
                    "url": "https://example.com/ai-power",
                    "source": "Example",
                    "description": "전력 인프라 투자가 늘었습니다.",
                }
            ],
        },
    )
    assert refresh.status_code == 200

    with database.get_connection() as db:
        candidate = db.execute("SELECT id FROM candidate_articles").fetchone()
        db.execute(
            """
            INSERT INTO ai_decisions (candidate_article_id, accepted, reason, summary, bullet_points)
            VALUES (?, 1, ?, ?, ?)
            """,
            (
                candidate["id"],
                "matched",
                "전력 인프라 투자가 늘었습니다.",
                json.dumps(["제목: AI 전력 수요 증가"], ensure_ascii=False),
            ),
        )
    return candidate["id"]


def test_scraps_are_scoped_and_reflected_in_dashboard(tmp_path, monkeypatch):
    client, database = build_client(tmp_path, monkeypatch)
    token = register(client, "user@example.com")
    other_token = register(client, "other@example.com")
    candidate_id = create_accepted_candidate(client, database, token)

    assert client.post(
        "/api/scraps",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"candidate_article_id": candidate_id},
    ).status_code == 404

    created = client.post(
        "/api/scraps",
        headers={"Authorization": f"Bearer {token}"},
        json={"candidate_article_id": candidate_id},
    )
    assert created.status_code == 201
    assert created.json()["candidate_article_id"] == candidate_id

    dashboard = client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"}).json()
    assert dashboard["articles"][0]["is_scrapped"] is True
    assert dashboard["scrapped_articles"][0]["candidate_article_id"] == candidate_id

    assert client.get("/api/scraps", headers={"Authorization": f"Bearer {other_token}"}).json() == []
    assert client.delete(f"/api/scraps/{candidate_id}", headers={"Authorization": f"Bearer {token}"}).status_code == 204
    assert client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"}).json()["scrapped_articles"] == []
