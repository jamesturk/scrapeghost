import os
import pytest
from unittest.mock import patch
from scrapeghost.scrapers import PaginatedSchemaScraper, _parse_url_or_html


page1 = """
<body>
<header>Site</header>
<main>
    <a href="/aardvark">Aardvark</a>
    <a href="/bear">Bear</a>
    <a href="/emu">Emu</a>
    <a href="/giraffe">Giraffe</a>
    <a href="/hippo">Hippo</a>
</main>
<footer>
    <a href="/page2">Next</a>
</footer>
"""


page2 = """
<body>
<header>Site</header>
<main>
    <a href="/iguana">Iguana</a>
    <a href="/jaguar">Jaguar</a>
    <a href="/koala">Koala</a>
    <a href="/lion">Lion</a>
    <a href="/narwhal">Narwhal</a>
</main>
<footer>
    <a href="/page1">Previous</a>
    <a href="/page3">Previous</a>
</footer>
"""


page3 = """
<body>
<header>Site</header>
<main>
    <a href="/tiger">Tiger</a>
    <a href="/vulture">Vulture</a>
    <a href="/whale">Whale</a>
    <a href="/yak">Yak</a>
</main>
<footer>
    <a href="/page2">Previous</a>
</footer>
"""

api_key_is_set = os.getenv("OPENAI_API_KEY", "")


@pytest.mark.skipif(not api_key_is_set, reason="requires API key")
def test_pagination():
    schema = {"name": "str", "url": "url"}
    scraper = PaginatedSchemaScraper(schema)

    orig = _parse_url_or_html
    with patch("scrapeghost.scrapers._parse_url_or_html") as parse:
        parse.side_effect = [orig(p) for p in (page1, page2, page3)]
        resp = scraper.scrape("https://example.com/page1")

    assert parse.call_args_list == [
        (("https://example.com/page1",),),
        (("/page2",),),
        (("/page3",),),
    ]
    print(resp.data)
    assert len(resp.data) == 14
    assert resp.data[0]["name"] == "Aardvark"
    assert resp.data[0]["url"] == "/aardvark"
    assert resp.data[-1]["name"] == "Yak"
    assert resp.data[-1]["url"] == "/yak"
