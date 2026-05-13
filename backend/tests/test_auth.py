import importlib

from fastapi.testclient import TestClient


def build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", str(tmp_path / "test.db"))
    from app import database
    from app import main

    importlib.reload(database)
    importlib.reload(main)
    main.init_db()
    return TestClient(main.app), database


def test_health_check(tmp_path, monkeypatch):
    client, _ = build_client(tmp_path, monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_me_and_logout(tmp_path, monkeypatch):
    client, database = build_client(tmp_path, monkeypatch)

    register_response = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "password123", "display_name": "User"},
    )

    assert register_response.status_code == 201
    token = register_response.json()["token"]
    assert register_response.json()["user"]["email"] == "user@example.com"

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["display_name"] == "User"

    login_response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token"] != token

    logout_response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_response.status_code == 200

    rejected_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert rejected_response.status_code == 401

    with database.get_connection() as db:
        row = db.execute("SELECT password_hash FROM users WHERE email = ?", ("user@example.com",)).fetchone()
    assert row["password_hash"] != "password123"
    assert row["password_hash"].startswith("pbkdf2_sha256$")


def test_schema_contains_required_tables(tmp_path, monkeypatch):
    _, database = build_client(tmp_path, monkeypatch)

    with database.get_connection() as db:
        table_rows = db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        columns = db.execute("PRAGMA table_info(interests)").fetchall()

    tables = {row["name"] for row in table_rows}
    assert {
        "users",
        "sessions",
        "interests",
        "hidden_keywords",
        "articles",
        "candidate_articles",
        "ai_decisions",
        "ai_jobs",
        "ai_workers",
        "article_reads",
    }.issubset(tables)
    assert "lookback_days" in {row["name"] for row in columns}
