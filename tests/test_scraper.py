import lxml.html
from scrapeghost import scrapers


def test_tostr():
    html = "<html><body>ventura</body></html>"
    doc = lxml.html.fromstring(html)
    assert scrapers._tostr(doc) == html


def test_chunk_tags():
    html = [
        lxml.html.fromstring("<li>one</li>"),
        lxml.html.fromstring("<li>two</li>"),
        lxml.html.fromstring("<li>three is very long and will get its own spot</li>"),
        lxml.html.fromstring("<li>four</li>"),
        lxml.html.fromstring("<li>five</li>"),
    ]
    chunks = scrapers._chunk_tags(html, 12, "gpt-4")
    assert len(chunks) == 3
    assert "one" in chunks[0]
    assert "two" in chunks[0]
    assert "three" in chunks[1]
    assert "four" in chunks[2]
    assert "five" in chunks[2]


def test_parse_html():
    # spaces are collapsed
    html = "<span>    ventura</span>"
    doc = scrapers._parse_url_or_html(html)
    assert scrapers._tostr(doc) == "<span> ventura</span>"


def test_parse_url():
    # test that requests are made
    url = "https://www.example.com"
    doc = scrapers._parse_url_or_html(url)
    assert doc.tag == "html"
