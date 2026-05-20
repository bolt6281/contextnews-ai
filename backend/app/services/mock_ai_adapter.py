import re


STOPWORDS = {"뉴스", "관련", "보고", "싶다", "대한", "있는", "없는", "그리고", "또는"}


def generate_hidden_keywords(keyword: str, description: str) -> list[str]:
    tokens = re.split(r"[\s,./·\-_:;()]+", description)
    keywords: list[str] = []
    for token in tokens:
        clean = token.strip()
        if len(clean) < 2 or clean in STOPWORDS:
            continue
        if clean not in keywords:
            keywords.append(clean)
        if len(keywords) >= 8:
            break
    if keyword not in keywords:
        keywords.insert(0, keyword)
    return keywords[:8]


def decide_article(interest: dict, article: dict, matched_keywords: list[str]) -> dict:
    accepted = bool(matched_keywords)
    keyword_text = ", ".join(matched_keywords[:3]) if matched_keywords else interest["keyword"]
    title = article["title"]
    source = article.get("source", "뉴스")
    return {
        "accepted": accepted,
        "reason": f"사용자의 관심 조건과 관련된 키워드({keyword_text})가 기사에서 확인되었습니다."
        if accepted
        else "사용자의 관심 조건과 직접적으로 겹치는 내용이 부족합니다.",
        "summary": f"{source}의 '{title}' 기사는 {interest['keyword']} 관련 흐름을 빠르게 확인할 수 있는 내용입니다."
        if accepted
        else "",
        "bullet_points": [
            f"관련 키워드: {keyword_text}",
            f"관심 조건: {interest['description'][:60]}",
            "원문 링크를 통해 자세한 내용을 확인할 수 있습니다.",
        ]
        if accepted
        else [],
    }
