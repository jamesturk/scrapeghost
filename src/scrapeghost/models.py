from dataclasses import dataclass


@dataclass
class Model:
    name: str
    prompt_token_cost: float  # $ per 1k input tokens, see https://openai.com/api/pricing
    completion_token_cost: float  # $ per 1k output tokens, see https://openai.com/api/pricing
    max_tokens: int  # max output tokens
    json_mode: bool  # see https://platform.openai.com/docs/guides/json-mode

    def cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens / 1000 * self.prompt_token_cost
            + completion_tokens / 1000 * self.completion_token_cost
        )


models = [
    Model("gpt-4", 0.03, 0.06, 8192, False),
    Model("gpt-4-32k", 0.06, 0.12, 32768, False),
    Model("gpt-4-1106-preview", 0.01, 0.03, 128000, True),
    Model("gpt-4-turbo", 0.01, 0.03, 4096, True),
    Model("gpt-4-turbo-preview", 0.01, 0.03, 4096, True),
    Model("gpt-4o", 0.005, 0.015, 4096, True),
    Model("gpt-4o-mini", 0.00015, 0.0006, 16384, True),
    Model("gpt-3.5-turbo", 0.001, 0.002, 16384, False),
    Model("gpt-3.5-turbo-1106", 0.001, 0.002, 16384, True),
]
_model_dict = {model.name: model for model in models}
