from __future__ import annotations
from typing import TYPE_CHECKING
import json
from .errors import InvalidJSON
from .response import Response

if TYPE_CHECKING:
    from .scrapers import SchemaScraper


class JSONPostprocessor:
    def __init__(self, nudge: bool = True):
        self.nudge = nudge

    def __call__(self, response: Response, scraper: SchemaScraper) -> Response:
        try:
            response.data = json.loads(response.data)
        except json.JSONDecodeError:
            response = self.nudge_json(scraper, response)
            try:
                response.data = json.loads(response.data)
            except json.JSONDecodeError:
                raise InvalidJSON("Invalid JSON: {data}")
        return response

    def nudge_json(self, scraper: SchemaScraper, response: Response) -> str:
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
                {"role": "user", "content": response.data},
            ],
            response,
        )


# class PydanticPostprocessor:
#     def __init__(self, model):
#         self.pydantic_model = model

#     def __call__(self, data: dict) -> dict:
#         return self.pydantic_model(**data).dict()
