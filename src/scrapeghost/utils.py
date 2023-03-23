import lxml.html
import structlog
import tiktoken


logger = structlog.get_logger("scrapeghost")


def _tostr(obj: lxml.html.HtmlElement) -> str:
    """
    Given lxml.html.HtmlElement, return string
    """
    return lxml.html.tostring(obj, encoding="unicode")


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pt_cost, ct_cost = {
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.002, 0.002),
    }[model]
    return prompt_tokens / 1000 * pt_cost + completion_tokens / 1000 * ct_cost


def _tokens(model: str, html: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(html))


def _max_tokens(model: str) -> int:
    return {
        "gpt-4": 8192,
        "gpt-3.5-turbo": 4096,
    }[model]


def cost_estimate(html: str, model: str = "gpt-4") -> float:
    """
    Given HTML, return cost estimate in dollars.

    This is a very rough estimate and not guaranteed to be accurate.
    """
    tokens = _tokens(model, html)
    # assumes response is half as long as prompt, which is probably wrong
    return _cost(model, tokens, tokens // 2)
