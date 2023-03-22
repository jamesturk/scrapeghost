import time
import json
import dataclasses
import openai
import openai.error
import lxml.html
from typing import Callable

from .errors import (
    TooManyTokens,
    MaxCostExceeded,
    PreprocessorError,
    BadStop,
)
from .response import Response
from .utils import (
    logger,
    _tostr,
    _chunk_tags,
    _parse_url_or_html,
    _combine_responses,
    _cost,
    _max_tokens,
    _tokens,
)
from .preprocessors import CleanHTML
from .postprocessors import JSONPostprocessor, PydanticPostprocessor

RETRY_ERRORS = (
    openai.error.RateLimitError,
    openai.error.Timeout,
    openai.error.APIConnectionError,
)


class SchemaScraper:
    _default_preprocessors: list[Callable] = [
        CleanHTML(),
    ]
    _default_postprocessors: list[Callable] = [
        JSONPostprocessor(),
    ]

    def __init__(
        self,
        schema: dict | str | list,
        *,
        # OpenAI parameters
        models: list[str] = ["gpt-3.5-turbo", "gpt-4"],
        model_params: dict | None = None,
        max_cost: float = 1,
        # instructions
        extra_instructions: list[str] | None = None,
        # preprocessing and postprocessing
        extra_preprocessors: list | None = None,
        postprocessors: list | None = None,
        auto_split_length: int = 0,
    ):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost: float = 0
        self.max_cost = max_cost
        self.models = models
        if model_params is None:
            model_params = {}
        self.model_params = model_params
        # default temperature to 0, deterministic
        if "temperature" not in model_params:
            model_params["temperature"] = 0

        use_pydantic = False
        if isinstance(schema, (list, dict)):
            self.json_schema = json.dumps(schema)
        elif isinstance(schema, str):
            self.json_schema = schema
        elif hasattr(schema, "schema"):
            self.json_schema = schema.schema()
            use_pydantic = True
        else:
            raise ValueError(f"Invalid schema: {schema}")

        if auto_split_length:
            json_type = "list of JSON objects"
        else:
            json_type = "JSON object"

        self.system_messages = [
            f"For the given HTML, convert to a {json_type} matching this schema: "
            f"{self.json_schema}",
            "Responses should be valid JSON, with no other text. "
            "Never truncate the JSON with an ellipsis. "
            "Always use double quotes for strings and escape quotes with \\. "
            "Always omit trailing commas. ",
        ]
        if extra_instructions:
            self.system_messages.extend(extra_instructions)

        if extra_preprocessors is None:
            self.preprocessors = self._default_preprocessors
        else:
            self.preprocessors = self._default_preprocessors + extra_preprocessors

        if postprocessors is None:
            self.postprocessors = self._default_postprocessors
            if use_pydantic:
                self.postprocessors.append(PydanticPostprocessor(schema))
        else:
            self.postprocessors = postprocessors

        self.auto_split_length = auto_split_length

    def _raw_api_request(
        self, model: str, messages: list[dict[str, str]], response: Response
    ) -> Response:
        """
        Make an OpenAPI request and return the raw response.

        * model - the OpenAI model to use
        * messages - the messages to send to the API
        * response - the Response object to augment

        Augments the response object with the API response, prompt tokens,
        completion tokens, and cost.
        """
        if self.total_cost > self.max_cost:
            raise MaxCostExceeded(
                f"Total cost {self.total_cost} exceeds max cost {self.max_cost}"
            )
        start_t = time.time()
        completion = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            **self.model_params,
        )
        elapsed = time.time() - start_t
        p_tokens = completion.usage.prompt_tokens
        c_tokens = completion.usage.completion_tokens
        cost = _cost(model, c_tokens, p_tokens)
        logger.info(
            "API response",
            duration=elapsed,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            finish_reason=completion.choices[0].finish_reason,
            cost=cost,
        )

        # Note: All modifications to response should be additive, so that
        #       this method can be called multiple times.
        response.api_responses.append(completion)
        response.total_prompt_tokens += p_tokens
        response.total_completion_tokens += c_tokens
        response.total_cost += cost
        response.api_time += elapsed
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
        response.data = choice.message.content
        return response

    def _api_request(self, html: str, response: Response) -> Response:
        """
        Make an OpenAPI request, with retries and model upgrades.

        * html - the HTML to send to the API
        * response - the Response object to augment
        """
        attempts = 0
        model_index = 0
        model = self.models[model_index]
        max_attempts = 2

        # make a copy so each request has its own response object
        response = dataclasses.replace(response)

        if not html:
            raise ValueError("html parameter cannot be empty")
        tokens = _tokens(model, html)
        if tokens > _max_tokens(model):
            raise TooManyTokens(
                f"HTML is {tokens} tokens, max for {model} is {_max_tokens(model)}"
            )

        while True:
            try:
                attempts += 1
                logger.info(
                    "API request",
                    model=model,
                    html_tokens=tokens,
                )
                self._raw_api_request(
                    model=model,
                    messages=[
                        {"role": "system", "content": msg}
                        for msg in self.system_messages
                    ]
                    + [
                        {"role": "user", "content": html},
                    ],
                    response=response,
                )
                return response
            except RETRY_ERRORS + (
                TooManyTokens,
                BadStop,
            ) as e:
                logger.warning(
                    "API request failed",
                    exception=str(e),
                    model=model,
                    attempts=attempts,
                )
                if attempts < max_attempts:
                    if isinstance(e, RETRY_ERRORS):
                        # try again with same model
                        # TODO: adjust sleep
                        time.sleep(60)
                        continue
                    elif model_index < len(self.models) - 1:
                        # try next model
                        model_index += 1
                        time.sleep(5)
                        continue
                # could not retry for whatever reason
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

    def _apply_postprocessors(self, response: Response) -> Response:
        # apply postprocessors
        for pp in self.postprocessors:
            response = pp(response, self)
        return response

    def scrape(
        self,
        url_or_html: str,
        extra_preprocessors: list | None = None,
    ) -> Response:
        """
        Scrape a URL and return a list or dict.

        Args:
            url: The URL to scrape.
            extra_preprocessors: A list of additional preprocessors to apply.

        Returns:
            dict | list: The scraped data in the specified schema.
        """
        response = Response()

        response.url = url_or_html if url_or_html.startswith("http") else None
        # obtain an HTML document from the URL or HTML string
        response.parsed_html = _parse_url_or_html(url_or_html)

        # apply preprocessors, returning a list of tags
        tags = self._apply_preprocessors(
            response.parsed_html, extra_preprocessors or []
        )

        response.auto_split_length = self.auto_split_length
        if self.auto_split_length:
            # if auto_split_length is set, split the tags into chunks
            chunks = _chunk_tags(tags, self.auto_split_length, model=self.models[0])

            # collect responses from each chunk
            all_responses = []
            for chunk in chunks:
                # make a copy so each chunk has its own response object
                response = dataclasses.replace(response)
                response = self._api_request(chunk, response)
                all_responses.append(self._apply_postprocessors(response))
            return _combine_responses(all_responses)
        else:
            # otherwise, scrape the whole document as one chunk
            html = "\n".join(_tostr(t) for t in tags)
            response = self._api_request(html, response)
            return self._apply_postprocessors(response)

    # allow the class to be called like a function
    __call__ = scrape

    def stats(self) -> dict:
        """
        Return stats about the scraper.
        """
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost": self.total_cost,
        }


# class PaginatedSchemaScraper(SchemaScraper):
#     def __init__(self, schema: list | str | dict, **kwargs: Any):
#         schema = {
#             "results": schema,
#             "next_link": "url",
#         }
#         super().__init__(schema, **kwargs)
#       self.system_messages.append("If there is no next page, set next_link to null.")

#     def scrape(self, url: str, **kwargs: Any):
#         results = []
#         seen_urls = set()
#         while url:
#             logger.debug("page", url=url)
#             page = super().scrape(url, **kwargs)
#             logger.debug(
#                 "results",
#                 next_link=page["next_link"],
#                 added_results=len(page["results"]),
#             )
#             results.extend(page["results"])
#             seen_urls.add(url)
#             url = page["next_link"]
#             if url in seen_urls:
#                 break
#         return results
