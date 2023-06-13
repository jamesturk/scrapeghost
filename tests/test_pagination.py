from unittest.mock import patch
from testutils import patch_create, _mock_response
from scrapeghost.scrapers import PaginatedSchemaScraper, _parse_url_or_html

resp1 = _mock_response(
    content="""{"next_page": "/page2", "results": [
        {"name": "Aardvark", "url": "/aardvark"}, {"name": "Bear", "url": "/bear"},
        {"name": "Emu", "url": "/emu"}, {"name": "Giraffe", "url": "/giraffe"},
        {"name": "Hippo", "url": "/hippo"}]}"""
)
resp2 = _mock_response(
    content="""{"next_page": "/page3", "results": [
        {"name": "Iguana", "url": "/iguana"}, {"name": "Jaguar", "url": "/jaguar"},
        {"name": "Koala", "url": "/koala"}, {"name": "Lion", "url": "/lion"},
        {"name": "Narwhal", "url": "/narwhal"}]}"""
)
resp3 = _mock_response(
    content="""{"next_page": null, "results": [
        {"name": "Tiger", "url": "/tiger"}, {"name": "Vulture", "url": "/vulture"},
        {"name": "Whale", "url": "/whale"}, {"name": "Yak", "url": "/yak"}]}"""
)

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


def test_pagination():
    schema = {"name": "str", "url": "url"}
    scraper = PaginatedSchemaScraper(schema)

    orig = _parse_url_or_html
    with patch("scrapeghost.scrapers._parse_url_or_html") as parse:
        with patch_create() as create:
            create.side_effect = [resp1, resp2, resp3]
            parse.side_effect = [orig(p) for p in (page1, page2, page3)]
            resp = scraper.scrape("https://example.com/page1")

    assert parse.call_args_list == [
        (("https://example.com/page1",),),
        (("/page2",),),
        (("/page3",),),
    ]
    assert len(resp.data) == 14
    assert resp.data[0]["name"] == "Aardvark"
    assert resp.data[0]["url"] == "/aardvark"
    assert resp.data[-1]["name"] == "Yak"
    assert resp.data[-1]["url"] == "/yak"

    assert resp.api_responses == [resp1, resp2, resp3]
    assert resp.total_cost == 0.0000105
    assert resp.total_prompt_tokens == 3
    assert resp.total_completion_tokens == 3
    assert resp.url == "/page2; /page3; https://example.com/page1"
