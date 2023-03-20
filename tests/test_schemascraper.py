import lxml.html
from scrapeghost import SchemaScraper, CSS
from scrapeghost.utils import _tostr


def test_apply_preprocessors_default():
    html = lxml.html.fromstring(
        "<html><script src='example.js' /><body>"
        "<span>1</span><span>2</span><span>3</span>"
        "</body></html>"
    )
    schema = SchemaScraper({})
    nodes = schema._apply_preprocessors(html, [])
    assert len(nodes) == 1
    assert (
        _tostr(nodes[0])
        == "<div><body><span>1</span><span>2</span><span>3</span></body></div>"
    )


def test_apply_preprocessors_constructor():
    html = lxml.html.fromstring(
        "<html><script src='example.js' /><body>"
        "<span>1</span><span>2</span><span>3</span>"
        "</body></html>"
    )
    schema = SchemaScraper({}, extra_preprocessors=[CSS("span")])
    nodes = schema._apply_preprocessors(html, [])
    assert len(nodes) == 3
    assert _tostr(nodes[0]) == "<span>1</span>"


def test_apply_preprocessors_extra():
    html = lxml.html.fromstring(
        "<html><script src='example.js' /><body>"
        "<span>1</span><span>2</span><span>3</span>"
        "</body></html>"
    )
    schema = SchemaScraper({})
    nodes = schema._apply_preprocessors(html, [CSS("span")])
    assert len(nodes) == 3
    assert _tostr(nodes[0]) == "<span>1</span>"
