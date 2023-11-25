from dataclasses import dataclass


@dataclass
class Model:
    name: str
    prompt_token_cost: float  # per 1k
    completion_token_cost: float  # per 1k
    max_tokens: int
    json_mode: bool

    def cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens / 1000 * self.prompt_token_cost
            + completion_tokens / 1000 * self.completion_token_cost
        )


models = [
    Model("gpt-4", 0.03, 0.06, 8192, False),
    Model("gpt-4-32k", 0.06, 0.12, 32768, False),
    Model("gpt-4-1106-preview", 0.01, 0.03, 128000, True),
    Model("gpt-3.5-turbo", 0.001, 0.002, 16384, False),
    Model("gpt-3.5-turbo-1106", 0.001, 0.002, 16384, True),
]
_model_dict = {model.name: model for model in models}
