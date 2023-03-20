import pytest
import lxml.html
from scrapeghost import utils


def test_tostr():
    html = "<html><body>ventura</body></html>"
    doc = lxml.html.fromstring(html)
    assert utils._tostr(doc) == html


def test_chunk_tags():
    html = [
        lxml.html.fromstring("<li>one</li>"),
        lxml.html.fromstring("<li>two</li>"),
        lxml.html.fromstring("<li>three is very long and will get its own spot</li>"),
        lxml.html.fromstring("<li>four</li>"),
        lxml.html.fromstring("<li>five</li>"),
    ]
    chunks = utils._chunk_tags(html, 12, "gpt-4")
    assert len(chunks) == 3
    assert "one" in chunks[0]
    assert "two" in chunks[0]
    assert "three" in chunks[1]
    assert "four" in chunks[2]
    assert "five" in chunks[2]


def test_parse_html():
    # spaces are collapsed
    html = "<span>    ventura</span>"
    doc = utils._parse_url_or_html(html)
    assert utils._tostr(doc) == "<span> ventura</span>"


def test_parse_url():
    # test that requests are made
    url = "https://www.example.com"
    doc = utils._parse_url_or_html(url)
    assert doc.tag == "html"


@pytest.mark.parametrize(
    "model,pt,ct,total",
    [
        ("gpt-4", 1000, 1000, 0.09),
        ("gpt-3.5-turbo", 1000, 1000, 0.004),
        ("gpt-3.5-turbo", 2000, 2000, 0.008),  # near max
        ("gpt-4", 4000, 4000, 0.36),  # near max
    ],
)
def test_cost_calc(model, pt, ct, total):
    assert utils._cost(model, pt, ct) == total


def test_cost_estimate():
    assert utils.cost_estimate("hello" * 1000, "gpt-3.5-turbo") == pytest.approx(0.003)
    assert utils.cost_estimate("hello" * 1000, "gpt-4") == pytest.approx(0.06)
