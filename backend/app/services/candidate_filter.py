import html
import re


TAG_RE = re.compile(r"<[^>]+>")


def normalize_text(value: str) -> str:
    unescaped = html.unescape(value or "")
    without_tags = TAG_RE.sub("", unescaped)
    return without_tags.lower()


def find_matched_keywords(title: str, description: str, hidden_keywords: list[str]) -> list[str]:
    text = normalize_text(f"{title} {description}")
    matched: list[str] = []
    for keyword in hidden_keywords:
        clean = keyword.strip()
        if clean and clean.lower() in text and clean not in matched:
            matched.append(clean)
    return matched


def is_candidate(title: str, description: str, hidden_keywords: list[str]) -> bool:
    return bool(find_matched_keywords(title, description, hidden_keywords))
