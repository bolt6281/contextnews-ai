import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.mock_ai_adapter import MockAIAdapter


def test_mock_ai_adapter_generates_hidden_keywords_from_description():
    adapter = MockAIAdapter()

    result = adapter.generate_hidden_keywords("AI", "반도체와 <b>전력</b> 인프라")

    assert result == {
        "hidden_keywords": ["AI", "반도체와", "전력", "인프라"],
        "provider": "mock",
    }


def test_mock_ai_adapter_returns_candidate_decision_from_matched_keywords():
    adapter = MockAIAdapter()
    article = {"title": "AI 전력 수요 증가", "url": "https://example.com/ai-power"}

    result = adapter.judge_candidate(article, ["전력"])

    assert result["accepted"] is True
    assert result["matched_keywords"] == ["전력"]
    assert result["article_url"] == "https://example.com/ai-power"


def test_mock_ai_adapter_returns_summary_and_bullet_points():
    adapter = MockAIAdapter()
    article = {
        "title": "AI 전력 수요 증가",
        "source": "Example",
        "description": "<p>데이터센터 전력 수요가 증가했습니다.</p>",
    }

    result = adapter.summarize(article)

    assert result["summary"] == "데이터센터 전력 수요가 증가했습니다."
    assert result["bullet_points"] == [
        "제목: AI 전력 수요 증가",
        "출처: Example",
        "요약: 데이터센터 전력 수요가 증가했습니다.",
    ]


def test_mock_ai_adapter_returns_backend_friendly_analysis_json():
    adapter = MockAIAdapter()
    article = {
        "title": "AI 전력 수요 증가",
        "url": "https://example.com/ai-power",
        "description": "전력 인프라 투자가 늘었습니다.",
    }

    result = adapter.analyze_candidate(article, ["전력"])

    assert set(result) == {"decision", "summary"}
    assert result["decision"]["accepted"] is True
    assert result["summary"]["summary"] == "전력 인프라 투자가 늘었습니다."
