from dataclasses import dataclass


@dataclass
class Response:
    api_responses: list
    total_cost: float
    total_prompt_tokens: int
    total_completion_tokens: int
    data: dict | list
