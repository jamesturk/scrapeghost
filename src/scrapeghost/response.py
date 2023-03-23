from dataclasses import dataclass, field
import lxml.html


@dataclass
class Response:
    api_responses: list = field(default_factory=list)
    total_cost: float = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    api_time: float = 0
    data: dict | list | str = ""


@dataclass
class ScrapeResponse(Response):
    url: str | None = None
    parsed_html: lxml.html.HtmlElement | None = None
    auto_split_length: int | None = None
