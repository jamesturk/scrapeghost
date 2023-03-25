from __future__ import annotations
from typing import TYPE_CHECKING

import json
from pydantic import ValidationError

from .utils import logger, _tostr
from .errors import InvalidJSON, PostprocessingError
from .responses import Response, ScrapeResponse

if TYPE_CHECKING:
    from .apicall import OpenAiCall
    from .scrapers import SchemaScraper


class JSONPostprocessor:
    def __init__(self, nudge: bool = True):
        self.nudge = nudge

    def __call__(self, response: Response, scraper: OpenAiCall) -> Response:
        if not isinstance(response.data, str):
            raise PostprocessingError(f"Response data is not a string: {response.data}")

        try:
            response.data = json.loads(response.data)
        except json.JSONDecodeError:
            if isinstance(scraper, SchemaScraper) and self.nudge:
                # call nudge and try again
                response = self.nudge_json(scraper, response)
                if not isinstance(response.data, str):
                    raise PostprocessingError(
                        f"Response data is not a string: {response.data}"
                    )
                try:
                    response.data = json.loads(response.data)
                except json.JSONDecodeError:
                    # if still invalid, raise error
                    raise InvalidJSON(response.data)
            else:
                raise InvalidJSON(response.data)
        return response

    def nudge_json(self, scraper: SchemaScraper, response: Response) -> Response:
        return scraper._raw_api_request(
            scraper.models[0],
            [
                {
                    "role": "system",
                    "content": (
                        "When you receive invalid JSON, "
                        "respond only with valid JSON matching the schema: "
                        f"{scraper.json_schema}"
                    ),
                },
                {"role": "system", "content": ("Only reply with JSON, nothing else. ")},
                {"role": "user", "content": "{'bad': 'json', }"},
                {"role": "assistant", "content": '{"bad": "json"}'},
                # response.data is always a string here
                {"role": "user", "content": response.data},  # type: ignore
            ],
            response,
        )


class PydanticPostprocessor:
    def __init__(self, model: type):
        self.pydantic_model = model

    def __call__(self, response: Response, scraper: OpenAiCall) -> Response:
        if not isinstance(response.data, dict):
            raise PostprocessingError(
                "PydanticPostprocessor expecting a dict, "
                "ensure JSONPostprocessor or equivalent is used first."
            )
        try:
            response.data = self.pydantic_model(**response.data)
        except ValidationError as e:
            logger.error("pydantic validation error", error=e, data=response.data)
            raise

        return response


class HallucinationChecker:
    """
    Check for data that is in the response that was not
    present on the page.

    Default behavior is to check all top-level strings.

    If you desire more control, subclass this class and
    register it as a postprocessor.
    """

    def __call__(self, response: Response, scraper: OpenAiCall) -> Response:
        if not isinstance(response, ScrapeResponse):
            raise PostprocessingError(
                "HallucinationChecker expects ScrapeResponse, "
                "Incompatible with auto_split_length"
            )
        if not isinstance(response.data, dict):
            raise PostprocessingError(
                "HallucinationChecker expecting a dict, "
                "ensure JSONPostprocessor or equivalent is used first."
            )
        html = _tostr(response.parsed_html)
        print(html)
        for key, value in response.data.items():
            if isinstance(value, str) and value not in html:
                raise PostprocessingError(
                    f"{key}={value} is not present in the response text"
                )
        return response
