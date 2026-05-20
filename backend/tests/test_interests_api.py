from fastapi.testclient import TestClient


def test_delete_interest_removes_owner_interest_and_pending_job(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'contextnews-test.db'}")

    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()

    with TestClient(app) as client:
        owner_headers = _register(client, "owner@example.com")
        other_headers = _register(client, "other@example.com")

        created = client.post(
            "/api/interests",
            headers=owner_headers,
            json={
                "keyword": "엔비디아",
                "description": "주가와 실적 관련 뉴스만 보고 싶다",
                "lookback_days": 7,
            },
        )
        assert created.status_code == 200
        interest_id = created.json()["id"]

        forbidden = client.delete(f"/api/interests/{interest_id}", headers=other_headers)
        assert forbidden.status_code == 404

        deleted = client.delete(f"/api/interests/{interest_id}", headers=owner_headers)
        assert deleted.status_code == 200
        assert deleted.json() == {"ok": True, "interest_id": interest_id}

        interests = client.get("/api/interests", headers=owner_headers)
        assert interests.status_code == 200
        assert interests.json() == {"interests": []}

        dashboard = client.get("/api/dashboard", headers=owner_headers)
        assert dashboard.status_code == 200
        assert dashboard.json()["stats"]["pending_ai_jobs"] == 0


def test_delete_interest_removes_pending_article_decision_jobs(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'contextnews-test.db'}")

    from app.config import get_settings
    from app.database import db_session
    from app.main import create_app
    from app.services.ai_job_service import create_ai_job

    get_settings.cache_clear()
    app = create_app()

    with TestClient(app) as client:
        owner_headers = _register(client, "owner-article-job@example.com")

        created = client.post(
            "/api/interests",
            headers=owner_headers,
            json={
                "keyword": "엔비디아",
                "description": "주가와 실적 관련 뉴스만 보고 싶다",
                "lookback_days": 7,
            },
        )
        assert created.status_code == 200
        interest_id = created.json()["id"]

        with db_session() as conn:
            user_id = conn.execute(
                "SELECT user_id FROM interests WHERE id = ?",
                (interest_id,),
            ).fetchone()["user_id"]

        article_job_id = create_ai_job(
            user_id,
            "article_decision",
            {
                "candidate_article_id": 123,
                "interest": {
                    "id": interest_id,
                    "keyword": "엔비디아",
                    "description": "주가와 실적 관련 뉴스만 보고 싶다",
                    "lookback_days": 7,
                },
                "article": {"title": "엔비디아 실적", "description": "실적 개선"},
                "matched_keywords": ["실적"],
            },
        )

        deleted = client.delete(f"/api/interests/{interest_id}", headers=owner_headers)
        assert deleted.status_code == 200

        with db_session() as conn:
            remaining = conn.execute(
                "SELECT id FROM ai_jobs WHERE id = ?",
                (article_job_id,),
            ).fetchone()
        assert remaining is None


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": "테스트",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['session_token']}"}
