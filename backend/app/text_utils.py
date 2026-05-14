import html
import re


HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def strip_html(value: str | None) -> str:
    if not value:
        return ""

    without_tags = HTML_TAG_RE.sub(" ", value)
    unescaped = html.unescape(without_tags)
    return WHITESPACE_RE.sub(" ", unescaped).strip()
