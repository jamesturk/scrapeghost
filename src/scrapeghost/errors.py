class ScrapeghostError(Exception):
    pass


class TooManyTokens(ScrapeghostError):
    pass


class MaxCostExceeded(ScrapeghostError):
    pass


class PreprocessorError(ScrapeghostError):
    pass


class BadStop(ScrapeghostError):
    pass


class NudgeableError(ScrapeghostError):
    def __init__(self, message: str, data: dict):
        self.message = message
        self.data = data

    def __str__(self):
        return self.message

    def nudge_message(self, schema):
        raise NotImplementedError


class InvalidJSON(NudgeableError):
    def nudge_message(self, schema):
        return [
            {
                "role": "system",
                "content": (
                    "When you receive invalid JSON, "
                    "respond only with valid JSON matching the schema: {schema}"
                ),
            },
            {"role": "system", "content": ("Only reply with JSON, nothing else. ")},
            {"role": "user", "content": "{'bad': 'json', }"},
            {"role": "assistant", "content": '{"bad": "json"}'},
            {"role": "user", "content": self.data},
        ]
