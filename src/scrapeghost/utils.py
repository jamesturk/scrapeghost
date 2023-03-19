import lxml.html
from lxml.html.clean import Cleaner
import structlog
import requests


logger = structlog.get_logger("scrapeghost")


def _tostr(obj: lxml.html.HtmlElement) -> str:
    """
    Given lxml.html.HtmlElement, return string
    """
    return lxml.html.tostring(obj, encoding="unicode")


def _chunk_tags(tags: list, auto_split: int) -> list[str]:
    """
    Given a list of all matching HTML tags, recombine into HTML chunks
    that can be passed to API.

    Returns list of strings, will always be len()==1 if auto_split is 0
    """
    pieces = []
    cur_piece = ""
    cur_piece_len = 0
    for tag in tags:
        tag_html = _tostr(tag)
        tag_len = len(tag_html)
        if cur_piece_len + tag_len > auto_split:
            pieces.append(cur_piece)
            cur_piece = ""
            cur_piece_len = 0
        cur_piece += tag_html
        cur_piece_len += tag_len

    pieces.append(cur_piece)
    logger.debug(
        "chunked tags",
        num=len(pieces),
        sizes=", ".join(str(len(c)) for c in pieces),
    )
    return pieces


def _parse_url_or_html(url_or_html: str) -> lxml.html.Element:
    """
    Given URL or HTML, return lxml.html.Element
    """
    # coerce to HTML
    orig_url = None
    if url_or_html.startswith("http"):
        orig_url = url_or_html
        url_or_html = requests.get(url_or_html).text
    logger.debug("got HTML", length=len(url_or_html), url=orig_url)
    url_or_html = Cleaner().clean_html(url_or_html)
    logger.debug("cleaned HTML", length=len(url_or_html))
    doc = lxml.html.fromstring(url_or_html)
    if orig_url:
        doc.make_links_absolute(orig_url)
    return doc


def _select_tags(
    doc: lxml.html.Element, xpath: str, css: str
) -> list[lxml.html.HtmlElement]:
    if xpath and css:
        raise ValueError("cannot specify both css and xpath")
    if xpath:
        tags = doc.xpath(xpath)
        sel = xpath
    elif css:
        tags = doc.cssselect(css)
        sel = css
    else:
        # so we can always return a list
        tags = [doc]
        sel = None

    if sel:
        logger.debug("selected tags", sel=sel, num=len(tags))
        if not len(tags):
            raise ValueError(f"empty results from {sel}")

    return tags
