import json
import time
import openai
import lxml.html
from .utils import (
    logger,
    _tostr,
    _chunk_tags,
    _parse_url_or_html,
    _cost,
    _max_tokens,
    _tokens,
)
from .preprocessors import CleanHTML


class MaxCostExceeded(Exception):
    pass


class PreprocessorError(Exception):
    pass


class BadStop(Exception):
    pass


class InvalidJSON(Exception):
    pass


class TooManyTokens(Exception):
    pass


class SchemaScraper:
    _default_preprocessors = [
        CleanHTML(),
    ]

    def __init__(
        self,
        schema: dict,
        *,
        # OpenAI parameters
        models: str = ["gpt-3.5-turbo", "gpt-4"],
        model_params: dict | None = None,
        max_cost: float = 1,
        # instructions
        list_mode: bool = False,
        extra_instructions: list[str] | None = None,
        # preprocessing
        preprocessors=None,
        split_length: int = 0,
    ):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0
        self.max_cost = max_cost
        self.models = models
        if model_params is None:
            model_params = {}
        self.model_params = model_params
        # default temperature to 0, deterministic
        if "temperature" not in model_params:
            model_params["temperature"] = 0

        if list_mode:
            self.system_messages = [
                "For the given HTML, convert to a list of JSON objects matching this schema: [{schema}]".format(
                    schema=json.dumps(schema)
                ),
            ]
        else:
            if split_length:
                raise ValueError("list_mode must be True if split_length is set")
            self.system_messages = [
                "For the given HTML, convert to a JSON object matching this schema: {schema}".format(
                    schema=json.dumps(schema)
                ),
            ]
        self.system_messages.append(
            "Responses should be valid JSON, with no other text. "
            "Never truncate the JSON with an ellipsis. "
            "Always use double quotes for strings and escape quotes with \\. Always omit trailing commas. "
        )
        if extra_instructions:
            self.system_messages.extend(extra_instructions)

        if preprocessors is None:
            self.preprocessors = self._default_preprocessors
        else:
            self.preprocessors = self._default_preprocessors + preprocessors
        self.split_length = split_length

    def _api_request(self, html: str, model: str) -> list | dict:
        """
        Given HTML, return JSON using OpenAI API
        """
        if not html:
            raise ValueError("html parameter cannot be empty")
        if self.total_cost > self.max_cost:
            raise MaxCostExceeded(
                f"Total cost {self.total_cost} exceeds max cost {self.max_cost}"
            )
        tokens = _tokens(model, html)
        if tokens > _max_tokens(model):
            raise TooManyTokens(
                f"HTML is {tokens} tokens, max for {model} is {_max_tokens(model)}"
            )
        logger.info(
            "API request",
            model=model,
            html_tokens=tokens,
            messages=self.system_messages,
        )
        start_t = time.time()
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": msg} for msg in self.system_messages
            ]
            + [
                {"role": "user", "content": html},
            ],
            **self.model_params,
        )
        p_tokens = completion.usage.prompt_tokens
        c_tokens = completion.usage.completion_tokens
        cost = _cost(model, c_tokens, p_tokens)
        logger.info(
            "API response",
            duration=time.time() - start_t,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            finish_reason=completion.choices[0].finish_reason,
            cost=cost,
        )
        self.total_prompt_tokens += p_tokens
        self.total_completion_tokens += c_tokens
        self.total_cost += cost
        choice = completion.choices[0]
        if choice.finish_reason != "stop":
            raise BadStop(
                f"OpenAI did not stop: {choice.finish_reason} "
                f"(prompt_tokens={p_tokens}, "
                f"completion_tokens={c_tokens})"
            )
        try:
            return json.loads(choice.message.content)
        except json.decoder.JSONDecodeError:
            raise InvalidJSON(choice.message.content)

    def _html_to_json(self, html: str) -> list | dict:
        for i, model in enumerate(self.models):
            last = i == len(self.models) - 1
            try:
                return self._api_request(html, model)
            except (openai.InvalidRequestError, BadStop, InvalidJSON) as e:
                logger.warning(
                    "API request failed",
                    exception=str(e),
                    model=model,
                )
                if last:
                    raise

    def _apply_preprocessors(
        self, doc: lxml.html.Element, extra_preprocessors: list
    ) -> list:
        nodes = [doc]

        # apply preprocessors one at a time
        for p in self.preprocessors + extra_preprocessors:
            new_nodes = []
            for node in nodes:
                new_nodes.extend(p(node))
            logger.debug(
                "preprocessor", name=str(p), from_nodes=len(nodes), nodes=len(new_nodes)
            )
            if not new_nodes:
                raise PreprocessorError(
                    f"Preprocessor {p} returned no nodes for {nodes}"
                )
            nodes = new_nodes

        return nodes

    def scrape(
        self,
        url_or_html: str,
        extra_preprocessors: list | None = None,
    ) -> dict | list:
        """
        Scrape a URL and return a list or dict.

        Args:
            url: The URL to scrape.
            extra_preprocessors: A list of additional preprocessors to apply.

        Returns:
            dict | list: The scraped data in the specified schema.
        """

        # obtain an HTML document from the URL or HTML string
        doc = _parse_url_or_html(url_or_html)

        # apply preprocessors, returning a list of tags
        tags = self._apply_preprocessors(doc, extra_preprocessors or [])

        if self.split_length:
            # if split_length is set, split the tags into chunks and scrape each chunk
            chunks = _chunk_tags(tags, self.split_length, model=self.models[0])
            # flatten list of lists
            return [item for chunk in chunks for item in self._html_to_json(chunk)]
        else:
            # otherwise, scrape the whole document as one chunk
            html = "\n".join(_tostr(t) for t in tags)
            return self._html_to_json(html)

    # allow the class to be called like a function
    __call__ = scrape


class PaginatedSchemaScraper(SchemaScraper):
    def __init__(self, schema, **kwargs):
        schema = {
            "results": schema,
            "next_link": "url",
        }
        super().__init__(schema, list_mode=False, **kwargs)
        self.system_messages.append("If there is no next page, set next_link to null.")

    def scrape(self, url, **kwargs):
        results = []
        seen_urls = set()
        while url:
            logger.debug("page", url=url)
            page = super().scrape(url, **kwargs)
            logger.debug(
                "results",
                next_link=page["next_link"],
                added_results=len(page["results"]),
            )
            results.extend(page["results"])
            seen_urls.add(url)
            url = page["next_link"]
            if url in seen_urls:
                break
        return results
