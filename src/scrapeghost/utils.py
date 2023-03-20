import lxml.html
from lxml.html.clean import Cleaner
import structlog
import requests
import tiktoken


logger = structlog.get_logger("scrapeghost")


def _tostr(obj: lxml.html.HtmlElement) -> str:
    """
    Given lxml.html.HtmlElement, return string
    """
    return lxml.html.tostring(obj, encoding="unicode")


def _chunk_tags(tags: list, max_tokens: int, model: str) -> list[str]:
    """
    Given a list of all matching HTML tags, recombine into HTML chunks
    that can be passed to API.
    """
    chunks = []
    chunk_sizes = []
    chunk = ""
    chunk_tokens = 0
    for tag in tags:
        tag_html = _tostr(tag)
        tag_tokens = _tokens(model, tag_html)
        if chunk_tokens + tag_tokens > max_tokens:
            chunks.append(chunk)
            chunk_sizes.append(chunk_tokens)
            chunk = ""
            chunk_tokens = 0
        chunk += tag_html
        chunk_tokens += tag_tokens

    chunks.append(chunk)
    chunk_sizes.append(chunk_tokens)
    logger.debug(
        "chunked tags",
        num=len(chunks),
        sizes=chunk_sizes,
    )
    return chunks


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


def _cost(model, prompt_tokens, completion_tokens):
    pt_cost, ct_cost = {
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.002, 0.002),
    }[model]
    return prompt_tokens / 1000 * pt_cost + completion_tokens / 1000 * ct_cost


def _tokens(model, html):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(html))


def _max_tokens(model):
    return {
        "gpt-4": 8192,
        "gpt-3.5-turbo": 4096,
    }[model]


def cost_estimate(html, model="gpt-4"):
    """
    Given HTML, return cost estimate in dollars.

    This is a very rough estimate and not guaranteed to be accurate.
    """
    tokens = _tokens(model, html)
    # assumes response is half as long as prompt, which is probably wrong
    return _cost(model, tokens, tokens / 2)
