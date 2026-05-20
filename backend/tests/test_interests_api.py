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


def test_interest_crud_is_scoped_to_current_user(tmp_path, monkeypatch):
    client, database = build_client(tmp_path, monkeypatch)
    user_token = register(client, "user@example.com")
    other_token = register(client, "other@example.com")

    created = client.post(
        "/api/interests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"keyword": "AI", "description": "반도체와 전력 인프라", "lookback_days": 14},
    )

    assert created.status_code == 201
    assert created.json()["keyword"] == "AI"
    assert created.json()["lookback_days"] == 14
    assert "hidden_keywords" not in created.json()

    assert client.get("/api/interests", headers={"Authorization": f"Bearer {user_token}"}).json()[0]["keyword"] == "AI"
    assert client.get("/api/interests", headers={"Authorization": f"Bearer {other_token}"}).json() == []
    assert client.delete(f"/api/interests/{created.json()['id']}", headers={"Authorization": f"Bearer {other_token}"}).status_code == 404

    with database.get_connection() as db:
        job = db.execute("SELECT job_type, payload FROM ai_jobs WHERE job_type = 'hidden_keywords'").fetchone()
    assert job["job_type"] == "hidden_keywords"
    assert json.loads(job["payload"])["interest_id"] == created.json()["id"]

    deleted = client.delete(f"/api/interests/{created.json()['id']}", headers={"Authorization": f"Bearer {user_token}"})

    assert deleted.status_code == 204
    assert client.get("/api/interests", headers={"Authorization": f"Bearer {user_token}"}).json() == []
