from fastapi.testclient import TestClient


def test_user_can_scrap_list_and_delete_accepted_article(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'contextnews-test.db'}")

    from app.config import get_settings
    from app.database import db_session
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()

    with TestClient(app) as client:
        owner_headers = _register(client, "owner@example.com")
        other_headers = _register(client, "other@example.com")

        with db_session() as conn:
            owner_id = conn.execute("SELECT id FROM users WHERE email = ?", ("owner@example.com",)).fetchone()["id"]
            other_id = conn.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",)).fetchone()["id"]
            owner_interest_id = conn.execute(
                """
                INSERT INTO interests (user_id, keyword, description, lookback_days)
                VALUES (?, ?, ?, ?)
                """,
                (owner_id, "엔비디아", "엔비디아 실적 관련 뉴스만 확인합니다.", 7),
            ).lastrowid
            other_interest_id = conn.execute(
                """
                INSERT INTO interests (user_id, keyword, description, lookback_days)
                VALUES (?, ?, ?, ?)
                """,
                (other_id, "엔비디아", "엔비디아 실적 관련 뉴스만 확인합니다.", 7),
            ).lastrowid
            article_id = conn.execute(
                """
                INSERT INTO articles (title, source, url, description, published_at, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "엔비디아 실적 전망 개선",
                    "Sample",
                    "https://example.com/nvidia",
                    "데이터센터 수요가 늘었습니다.",
                    "2026-05-15T12:00:00+00:00",
                    "{}",
                ),
            ).lastrowid
            owner_candidate_id = conn.execute(
                """
                INSERT INTO candidate_articles (interest_id, article_id, matched_keywords)
                VALUES (?, ?, ?)
                """,
                (owner_interest_id, article_id, '["실적"]'),
            ).lastrowid
            other_candidate_id = conn.execute(
                """
                INSERT INTO candidate_articles (interest_id, article_id, matched_keywords)
                VALUES (?, ?, ?)
                """,
                (other_interest_id, article_id, '["실적"]'),
            ).lastrowid
            for candidate_id in (owner_candidate_id, other_candidate_id):
                conn.execute(
                    """
                    INSERT INTO ai_decisions
                      (candidate_article_id, accepted, reason, summary, bullet_points, ai_mode)
                    VALUES (?, 1, ?, ?, ?, ?)
                    """,
                    (candidate_id, "관심 조건에 맞습니다.", "요약입니다.", '["핵심 1"]', "mock"),
                )

        dashboard = client.get("/api/dashboard", headers=owner_headers)
        assert dashboard.status_code == 200
        item = dashboard.json()["items"][0]
        assert item["candidate_article_id"] == owner_candidate_id
        assert item["is_scrapped"] is False

        created = client.post("/api/scraps", headers=owner_headers, json={"candidate_article_id": owner_candidate_id})
        assert created.status_code == 200
        assert created.json()["ok"] is True
        assert created.json()["candidate_article_id"] == owner_candidate_id

        scraps = client.get("/api/scraps", headers=owner_headers)
        assert scraps.status_code == 200
        scrap_items = scraps.json()["items"]
        assert len(scrap_items) == 1
        assert scrap_items[0]["candidate_article_id"] == owner_candidate_id
        assert scrap_items[0]["is_scrapped"] is True
        assert scrap_items[0]["scrapped_at"]

        dashboard_after_scrap = client.get("/api/dashboard", headers=owner_headers)
        assert dashboard_after_scrap.status_code == 200
        assert dashboard_after_scrap.json()["items"][0]["is_scrapped"] is True

        forbidden_delete = client.delete(f"/api/scraps/{owner_candidate_id}", headers=other_headers)
        assert forbidden_delete.status_code == 404

        owner_can_delete_only_their_candidate = client.delete(f"/api/scraps/{other_candidate_id}", headers=owner_headers)
        assert owner_can_delete_only_their_candidate.status_code == 404

        deleted = client.delete(f"/api/scraps/{owner_candidate_id}", headers=owner_headers)
        assert deleted.status_code == 200
        assert deleted.json() == {"ok": True, "candidate_article_id": owner_candidate_id}

        empty_scraps = client.get("/api/scraps", headers=owner_headers)
        assert empty_scraps.status_code == 200
        assert empty_scraps.json()["items"] == []

        dashboard_after_delete = client.get("/api/dashboard", headers=owner_headers)
        assert dashboard_after_delete.status_code == 200
        assert dashboard_after_delete.json()["items"][0]["is_scrapped"] is False


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
