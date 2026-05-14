from app.ai_adapter import ArticleInput, CandidateInput, TestAIAdapter


def test_test_ai_adapter_generates_hidden_keywords_from_description():
    adapter = TestAIAdapter()

    result = adapter.generate_hidden_keywords("AI", "반도체와 <b>전력</b> 인프라")

    assert result.hidden_keywords == ["AI", "반도체와", "전력", "인프라"]


def test_test_ai_adapter_accepts_candidate_by_matched_keywords():
    adapter = TestAIAdapter()
    article = ArticleInput(
        title="AI 전력 수요 증가",
        url="https://example.com/ai-power",
        source="Example",
        description="데이터센터 전력 수요가 증가했습니다.",
    )
    candidate = CandidateInput(article=article, matched_keywords=["전력"])

    result = adapter.analyze_candidate(candidate)

    assert result.decision.accepted is True
    assert result.decision.matched_keywords == ["전력"]
    assert result.summary.summary == "데이터센터 전력 수요가 증가했습니다."
    assert result.summary.bullet_points
