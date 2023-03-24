import lxml.html
import lxml.html.clean
from typing import Callable


Preprocessor = Callable[[lxml.html.HtmlElement], list[lxml.html.HtmlElement]]


class CleanHTML:
    """
    Given HTML, return a cleaned HTML string.

    Uses lxml.html.clean.Cleaner.
    """

    def __init__(self, **kwargs: dict) -> None:
        # need to set remove_unknown_tags to False since lxml.html seems to
        # have an outdated list of tags
        self.cleaner = lxml.html.clean.Cleaner(**kwargs, remove_unknown_tags=False)

    def __str__(self) -> str:
        return "CleanHTML"

    def __call__(self, doc: lxml.html.Element) -> lxml.html.Element:
        self.cleaner(doc)
        return [doc]


class XPath:
    """
    Given an XPath selector, return a list of nodes.
    """

    def __init__(self, xpath: str):
        self.xpath = xpath

    def __str__(self) -> str:
        return f"XPath({self.xpath})"

    def __call__(self, node: lxml.html.HtmlElement) -> list[lxml.html.HtmlElement]:
        return node.xpath(self.xpath)


class CSS:
    """
    Given a CSS selector, return a list of nodes.
    """

    def __init__(self, css: str):
        self.css = css

    def __str__(self) -> str:
        return f"CSS({self.css})"

    def __call__(self, node: lxml.html.HtmlElement) -> list[lxml.html.HtmlElement]:
        return node.cssselect(self.css)
