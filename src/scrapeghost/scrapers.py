import re
import json
import typing
import requests
import lxml.html

from typing import Any, Sequence, Type
from pydantic import BaseModel
from .errors import PreprocessorError
from .responses import Response, ScrapeResponse
from .apicall import OpenAiCall, Postprocessor, RetryRule
from .utils import logger, _tokens, _tostr
from .preprocessors import Preprocessor, CleanHTML
from .postprocessors import (
    JSONPostprocessor,
    PydanticPostprocessor,
)


class SchemaScraper(OpenAiCall):
    _default_preprocessors: list[Preprocessor] = [
        CleanHTML(),
    ]

    def __init__(
        self,
        schema: dict | str | list,
        extra_preprocessors: list | None = None,
        *,
        auto_split_length: int = 0,
        # inherited from OpenAiCall
        models: list[str] = ["gpt-3.5-turbo", "gpt-4"],
        model_params: dict | None = None,
        max_cost: float = 1,
        retry: RetryRule = RetryRule(1, 30),
        extra_instructions: list[str] | None = None,
        postprocessors: list | None = None,
    ):
        # extra_instructions & postprocessors handled
        # differently in SchemaScraper so not passed to super()
        super().__init__(
            models=models, model_params=model_params, max_cost=max_cost, retry=retry
        )
        use_pydantic = False
        if isinstance(schema, (list, dict)):
            self.json_schema = json.dumps(schema)
        elif isinstance(schema, str):
            self.json_schema = schema
        elif hasattr(schema, "schema"):
            self.json_schema = _pydantic_to_simple_schema(schema)
            use_pydantic = True
        else:  # pragma: no cover
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
            ]

        if postprocessors is None:
            self.postprocessors = _default_postprocessors
        else:
            self.postprocessors = postprocessors

        self.system_messages = [
            f"For the given HTML, convert to a {json_type} matching this schema: "
            f"{self.json_schema}",
            "Limit responses to valid JSON, with no explanatory text. "
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
            # check if schema is a pydantic model
            if not isinstance(schema, type) or not issubclass(schema, BaseModel):
                raise ValueError("Schema must be a Pydantic model.")
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


def _combine_responses(
    sr: ScrapeResponse, responses: Sequence[Response]
) -> ScrapeResponse:
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


def _pydantic_to_simple_schema(pydantic_model: Type[BaseModel]) -> dict:
    """
    Given a Pydantic model, return a simple schema that can be used
    by SchemaScraper.

    We don't use Pydantic's schema() method because the
    additional complexity of JSON Schema adds a lot of extra tokens
    and in testing did not work as well as the simplified versions.
    """
    schema: dict = {}
    for field_name, field in pydantic_model.model_fields.items():
        # model_fields is present on Pydantic models, so can process recursively
        if field.annotation is None:
            raise TypeError("missing annotation")
        elif isinstance(field.annotation, type) and issubclass(
            field.annotation, BaseModel
        ):
            schema[field_name] = _pydantic_to_simple_schema(field.annotation)
        else:
            type_name = field.annotation.__name__
            if type_name == "list":
                (inner,) = typing.get_args(field.annotation)
                schema[field_name] = [inner.__name__]
            elif type_name == "dict":
                k, v = typing.get_args(field.annotation)
                schema[field_name] = {k.__name__: v.__name__}
            else:
                schema[field_name] = type_name
    return schema


class PaginatedSchemaScraper(SchemaScraper):
    def __init__(self, schema: list | str | dict, **kwargs: Any):
        # modify schema to include next_page_link
        schema = {
            "results": schema,
            "next_page": "url",
        }
        super().__init__(schema, **kwargs)
        self.system_messages.append("If there is no next page, set next_page to null.")

    def scrape(
        self, url: str, extra_preprocessors: list | None = None
    ) -> ScrapeResponse:
        sr = ScrapeResponse()
        responses = []
        seen_urls = set([url])
        while url:
            logger.debug("page", url=url)
            resp = super().scrape(url, extra_preprocessors=extra_preprocessors)
            # modify response to remove next_page wrapper
            if isinstance(resp.data, dict):
                url = resp.data["next_page"]
                resp.data = resp.data["results"]
            else:  # pragma: no cover
                raise ValueError("PaginatedSchemaScraper requires object response")
            responses.append(resp)
            logger.debug(
                "page results",
                next_page=url,
                added_results=len(resp.data),
            )
            if url in seen_urls:
                break
            if url:
                seen_urls.add(url)

        sr.url = "; ".join(sorted(seen_urls))
        return _combine_responses(sr, responses)
