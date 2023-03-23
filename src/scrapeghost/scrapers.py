import re
import json
import dataclasses
import requests
import lxml.html
from typing import Callable

from .errors import (
    PreprocessorError,
)
from .response import Response, ScrapeResponse
from .utils import (
    logger,
    _tostr,
    _tokens,
    _pydantic_to_simple_schema,
)
from .preprocessors import CleanHTML
from .postprocessors import JSONPostprocessor, PydanticPostprocessor
from .apicall import OpenAiCall


class SchemaScraper(OpenAiCall):
    _default_preprocessors: list[Callable] = [
        CleanHTML(),
    ]
    _default_postprocessors: list[Callable] = [
        JSONPostprocessor(),
    ]

    def __init__(
        self,
        schema: dict | str | list,
        extra_preprocessors: list | None = None,
        *,
        auto_split_length: int = 0,
        extra_instructions: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        use_pydantic = False
        if isinstance(schema, (list, dict)):
            self.json_schema = json.dumps(schema)
        elif isinstance(schema, str):
            self.json_schema = schema
        elif hasattr(schema, "schema"):
            self.json_schema = _pydantic_to_simple_schema(schema)
            use_pydantic = True
        else:
            raise ValueError(f"Invalid schema: {schema}")

        if auto_split_length:
            json_type = "list of JSON objects"
        else:
            json_type = "JSON object"

        self.system_messages = [
            f"For the given HTML, convert to a {json_type} matching this schema: "
            f"{self.json_schema}",
            "Responses should be valid JSON, with no other text. "
            "Never truncate the JSON with an ellipsis. "
            "Always use double quotes for strings and escape quotes with \\. "
            "Always omit trailing commas. ",
        ]
        if extra_instructions:
            self.system_messages.extend(extra_instructions)

        if extra_preprocessors is None:
            self.preprocessors = self._default_preprocessors
        else:
            self.preprocessors = self._default_preprocessors + extra_preprocessors

        if use_pydantic:
            self.postprocessors.append(PydanticPostprocessor(schema))

        self.auto_split_length = auto_split_length

    def _apply_preprocessors(
        self, doc: lxml.html.Element, extra_preprocessors: list
    ) -> list:
        nodes = [doc]

        # apply preprocessors one at a time
        for p in self.preprocessors + extra_preprocessors:
            new_nodes = []
            for node in nodes:
                new_nodes.extend(p(node))
            logger.debug(
                "preprocessor", name=str(p), from_nodes=len(nodes), nodes=len(new_nodes)
            )
            if not new_nodes:
                raise PreprocessorError(
                    f"Preprocessor {p} returned no nodes for {nodes}"
                )
            nodes = new_nodes

        return nodes

    def scrape(
        self,
        url_or_html: str,
        extra_preprocessors: list | None = None,
    ) -> ScrapeResponse:
        """
        Scrape a URL and return a list or dict.

        Args:
            url: The URL to scrape.
            extra_preprocessors: A list of additional preprocessors to apply.

        Returns:
            dict | list: The scraped data in the specified schema.
        """
        response = ScrapeResponse()

        response.url = url_or_html if url_or_html.startswith("http") else None
        # obtain an HTML document from the URL or HTML string
        response.parsed_html = _parse_url_or_html(url_or_html)

        # apply preprocessors, returning a list of tags
        tags = self._apply_preprocessors(
            response.parsed_html, extra_preprocessors or []
        )

        response.auto_split_length = self.auto_split_length
        if self.auto_split_length:
            # if auto_split_length is set, split the tags into chunks
            chunks = _chunk_tags(tags, self.auto_split_length, model=self.models[0])

            # collect responses from each chunk
            all_responses = []
            for chunk in chunks:
                # make a copy so each chunk has its own response object
                response = dataclasses.replace(response)
                response = self._api_request(chunk, response)
                all_responses.append(self._apply_postprocessors(response))
            return _combine_responses(all_responses)
        else:
            # otherwise, scrape the whole document as one chunk
            html = "\n".join(_tostr(t) for t in tags)
            response = self._api_request(html, response)
            return self._apply_postprocessors(response)

    # allow the class to be called like a function
    __call__ = scrape


def _combine_responses(sr: ScrapeResponse, responses: list[Response]) -> ScrapeResponse:
    """
    Combine (possibly paginated) API responses into a single ScrapeResponse.
    """
    sr.api_responses = [
        api_resp for resp in responses for api_resp in resp.api_responses
    ]
    sr.total_cost = sum([resp.total_cost for resp in responses])
    sr.total_prompt_tokens = sum([resp.total_prompt_tokens for resp in responses])
    sr.total_completion_tokens = sum(
        [resp.total_completion_tokens for resp in responses]
    )
    sr.pi_time = sum([resp.api_time for resp in responses])
    sr.data = [item for resp in responses for item in resp.data]


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


# class PaginatedSchemaScraper(SchemaScraper):
#     def __init__(self, schema: list | str | dict, **kwargs: Any):
#         schema = {
#             "results": schema,
#             "next_link": "url",
#         }
#         super().__init__(schema, **kwargs)
#       self.system_messages.append("If there is no next page, set next_link to null.")

#     def scrape(self, url: str, **kwargs: Any):
#         results = []
#         seen_urls = set()
#         while url:
#             logger.debug("page", url=url)
#             page = super().scrape(url, **kwargs)
#             logger.debug(
#                 "results",
#                 next_link=page["next_link"],
#                 added_results=len(page["results"]),
#             )
#             results.extend(page["results"])
#             seen_urls.add(url)
#             url = page["next_link"]
#             if url in seen_urls:
#                 break
#         return results
