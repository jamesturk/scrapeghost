import lxml.html
from scrapeghost.preprocessors import CleanHTML, XPath, CSS
from scrapeghost.utils import _tostr


def test_clean_html():
    doc = lxml.html.fromstring(
        "<html><body style='background: blue;'><script>alert('hello')</script><noscript>here</noscript></body></html>"
    )
    tags = CleanHTML()(doc)
    assert len(tags) == 1
    doc = tags[0]
    assert _tostr(doc) == "<div><body><noscript>here</noscript></body></div>"


def test_select_tags_css():
    doc = lxml.html.fromstring(
        "<html><body><p>one</p><p>two</p><p>three</p></body></html>"
    )
    tags = CSS("p")(doc)
    assert len(tags) == 3


def test_select_tags_xpath():
    doc = lxml.html.fromstring(
        "<html><body><p>one</p><p>two</p><p>three</p></body></html>"
    )
    tags = XPath("//p")(doc)
    assert len(tags) == 3
