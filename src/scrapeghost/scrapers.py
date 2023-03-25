import re
import json
import requests
import lxml.html

from .errors import PreprocessorError
from .responses import Response, ScrapeResponse
from .apicall import OpenAiCall, Postprocessor
from .utils import logger, _tokens, _tostr
from .preprocessors import Preprocessor, CleanHTML
from .postprocessors import (
    JSONPostprocessor,
    PydanticPostprocessor,
    HallucinationChecker,
)


class SchemaScraper(OpenAiCall):
    _default_preprocessors: list[Preprocessor] = [
        CleanHTML(),
    ]

    def __init__(  # type: ignore
        self,
        schema: dict | str | list,
        extra_preprocessors: list | None = None,
        *,
        auto_split_length: int = 0,
        extra_instructions: list[str] | None = None,
        postprocessors: list[Postprocessor] | None = None,
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

        _default_postprocessors: list[Postprocessor]
        if auto_split_length:
            json_type = "list of JSON objects"
            _default_postprocessors = [
                JSONPostprocessor(nudge=False),
            ]
        else:
            json_type = "JSON object"
            _default_postprocessors = [
                JSONPostprocessor(nudge=True),
                HallucinationChecker(),
            ]

        if postprocessors is None:
            self.postprocessors = _default_postprocessors
        else:
            self.postprocessors = _default_postprocessors + postprocessors

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
            self.postprocessors.append(PydanticPostprocessor(schema))  # type: ignore

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
        sr = ScrapeResponse()

        sr.url = url_or_html if url_or_html.startswith("http") else None
        # obtain an HTML document from the URL or HTML string
        sr.parsed_html = _parse_url_or_html(url_or_html)

        # apply preprocessors, returning a list of tags
        tags = self._apply_preprocessors(sr.parsed_html, extra_preprocessors or [])

        sr.auto_split_length = self.auto_split_length
        if self.auto_split_length:
            # if auto_split_length is set, split the tags into chunks and then recombine
            chunks = _chunk_tags(tags, self.auto_split_length, model=self.models[0])
            # Note: this will not work when the postprocessor is expecting
            # ScrapedResponse (like HallucinationChecker)
            all_responses = [self.request(chunk) for chunk in chunks]
            return _combine_responses(sr, all_responses)
        else:
            # otherwise, scrape the whole document as one chunk
            html = "\n".join(_tostr(t) for t in tags)
            # apply postprocessors to the ScrapeResponse
            # so that they can access the parsed HTML if needed
            return self._apply_postprocessors(  # type: ignore
                _combine_responses(sr, [self._api_request(html)])
            )

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
    sr.api_time = sum([resp.api_time for resp in responses])
    if len(responses) > 1:
        sr.data = [item for resp in responses for item in resp.data]
    else:
        sr.data = responses[0].data
    return sr


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
