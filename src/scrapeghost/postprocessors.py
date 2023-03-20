import json
from .errors import InvalidJSON


class JSONPostprocessor:
    def __call__(self, data: str) -> dict:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            raise InvalidJSON("Invalid JSON: {data}")
