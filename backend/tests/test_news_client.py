import xml.etree.ElementTree as ET

from app.services.news_client import _parse_google_item


# Google News RSS item이 내부 article 응답 구조로 정규화되는지 검증한다.
def test_parse_google_item_normalizes_rss_item():
    item = ET.fromstring(
        """
        <item>
          <title>엔비디아 실적 전망 개선 - Sample Source</title>
          <link>https://news.google.com/rss/articles/sample</link>
          <pubDate>Mon, 11 May 2026 12:00:00 GMT</pubDate>
          <source url="https://example.com">Sample Source</source>
          <description>&lt;a href="https://example.com"&gt;기사&lt;/a&gt; 설명입니다.</description>
        </item>
        """
    )

    parsed = _parse_google_item(item)

    assert parsed is not None
    assert parsed["title"] == "엔비디아 실적 전망 개선"
    assert parsed["source"] == "Sample Source"
    assert parsed["description"] == "기사 설명입니다."
    assert parsed["raw_payload"]
