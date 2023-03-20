import json
from .errors import InvalidJSON


class JSONPostprocessor:
    def __init__(self, nudge=True):
        self.nudge = nudge

    def __call__(self, data: str, scraper) -> dict:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            data = self.nudge_json(scraper, data)
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise InvalidJSON("Invalid JSON: {data}")

    def nudge_json(self, scraper, data):
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
                {"role": "user", "content": data},
            ],
        )


class PydanticPostprocessor:
    def __init__(self, model):
        self.pydantic_model = model

    def __call__(self, data: dict) -> dict:
        return self.pydantic_model(**data).dict()
