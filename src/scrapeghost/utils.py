import re
import lxml.html
import lxml.html.clean
import structlog
import requests
import tiktoken
from .response import Response


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
        # if adding tag would exceed max_tokens, start new chunk (unless chunk is empty)
        if chunk_tokens + tag_tokens > max_tokens and chunk_tokens > 0:
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
    # collapse whitespace
    url_or_html = re.sub("[ \t]+", " ", url_or_html)
    logger.debug("got HTML", length=len(url_or_html), url=orig_url)
    doc = lxml.html.fromstring(url_or_html)
    if orig_url:
        doc.make_links_absolute(orig_url)
    return doc


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pt_cost, ct_cost = {
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.002, 0.002),
    }[model]
    return prompt_tokens / 1000 * pt_cost + completion_tokens / 1000 * ct_cost


def _tokens(model: str, html: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(html))


def _max_tokens(model: str) -> int:
    return {
        "gpt-4": 8192,
        "gpt-3.5-turbo": 4096,
    }[model]


def cost_estimate(html: str, model: str = "gpt-4") -> float:
    """
    Given HTML, return cost estimate in dollars.

    This is a very rough estimate and not guaranteed to be accurate.
    """
    tokens = _tokens(model, html)
    # assumes response is half as long as prompt, which is probably wrong
    return _cost(model, tokens, tokens // 2)


def _combine_responses(responses: list[Response]) -> Response:
    """
    Given a list of Response objects, return a single Response object
    that combines all the data.
    """
    return Response(
        url=responses[0].url,
        parsed_html=responses[0].parsed_html,
        auto_split_length=responses[0].auto_split_length,
        api_responses=[
            api_resp for resp in responses for api_resp in resp.api_responses
        ],
        total_cost=sum([resp.total_cost for resp in responses]),
        total_prompt_tokens=sum([resp.total_prompt_tokens for resp in responses]),
        total_completion_tokens=sum(
            [resp.total_completion_tokens for resp in responses]
        ),
        api_time=sum([resp.api_time for resp in responses]),
        data=[item for resp in responses for item in resp.data],
    )


def _pydantic_to_simple_schema(pydantic_model: type) -> dict:
    """
    Given a Pydantic model, return a simple schema that can be used
    by SchemaScraper.

    We don't use Pydantic's schema() method because the
    additional complexity of JSON Schema adds a lot of extra tokens
    and in testing did not work as well as the simplified versions.
    """
    schema = {}
    for field in pydantic_model.__fields__.values():  # type: ignore
        if hasattr(field.outer_type_, "__fields__"):
            schema[field.name] = _pydantic_to_simple_schema(field.outer_type_)
        else:
            type_name = field.outer_type_.__name__
            if type_name == "list":
                type_name += f"[{field.type_.__name__}]"
            schema[field.name] = type_name
    return schema
