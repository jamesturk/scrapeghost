from dataclasses import dataclass, field
import lxml.html


@dataclass
class Response:
    url: str | None = None
    parsed_html: lxml.html.HtmlElement | None = None
    auto_split_length: int | None = None
    api_responses: list = field(default_factory=list)
    cost: float = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    api_time: float = 0
    data: dict | list | None = None
