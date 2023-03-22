from __future__ import annotations
from typing import TYPE_CHECKING
import json
from .errors import InvalidJSON, PostprocessingError
from .response import Response

if TYPE_CHECKING:
    from .scrapers import SchemaScraper


class JSONPostprocessor:
    def __init__(self, nudge: bool = True):
        self.nudge = nudge

    def __call__(self, response: Response, scraper: SchemaScraper) -> Response:
        if not isinstance(response.data, str):
            raise PostprocessingError(f"Response data is not a string: {response.data}")

        try:
            response.data = json.loads(response.data)
        except json.JSONDecodeError:
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
    def __init__(self, model):
        self.pydantic_model = model

    def __call__(self, response: Response, scraper: SchemaScraper) -> Response:
        if not isinstance(response.data, dict):
            raise PostprocessingError(
                "PydanticPostprocessor expecting a dict, "
                "ensure JSONPostprocessor or equivalent is used first."
            )
        # will raise pydantic ValidationError if invalid
        response.data = self.pydantic_model(**response.data)
        return response
