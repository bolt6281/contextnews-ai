from app.routers.refresh import _build_news_search_query


def test_build_news_search_query_uses_specific_hidden_keyword():
    interest = {"keyword": "엔비디아"}

    query = _build_news_search_query(
        interest,
        ["엔비디아 양자컴퓨터", "양자컴퓨터", "AI"],
    )

    assert query == "엔비디아 양자컴퓨터"


def test_build_news_search_query_combines_keyword_with_context_keyword():
    interest = {"keyword": "엔비디아"}

    query = _build_news_search_query(
        interest,
        ["CUDA-Q", "양자컴퓨터"],
    )

    assert query == "엔비디아 CUDA-Q"
