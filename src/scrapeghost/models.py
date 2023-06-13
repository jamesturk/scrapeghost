from dataclasses import dataclass


@dataclass
class Model:
    name: str
    prompt_token_cost: float  # per 1k
    completion_token_cost: float  # per 1k
    max_tokens: int

    def cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens / 1000 * self.prompt_token_cost
            + completion_tokens / 1000 * self.completion_token_cost
        )


models = [
    Model("gpt-4", 0.03, 0.06, 8192),
    Model("gpt-4-32k", 0.06, 0.12, 32768),
    Model("gpt-3.5-turbo", 0.0015, 0.002, 4096),
    Model("gpt-3.5-turbo-16k", 0.003, 0.004, 16384),
    Model("gpt-3.5-turbo-0613", 0.0015, 0.002, 4096),
    Model("gpt-3.5-turbo-16k-0613", 0.003, 0.004, 16384),
]
_model_dict = {model.name: model for model in models}
