"""
Module for making OpenAI API calls.
"""
import os
import time
import openai
from dataclasses import dataclass
from openai import OpenAI
from typing import Callable

from .errors import (
    ScrapeghostError,
    TooManyTokens,
    MaxCostExceeded,
    BadStop,
)
from .responses import Response
from .utils import (
    logger,
    _tokens,
)
from .models import _model_dict

Postprocessor = Callable[[Response, "OpenAiCall"], Response]


RETRY_ERRORS = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
)


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))


@dataclass
class RetryRule:
    max_retries: int = 0
    retry_wait: int = 30  # seconds
    retry_errors: tuple = RETRY_ERRORS


class OpenAiCall:
    _default_postprocessors: list[Postprocessor] = []

    def __init__(
        self,
        *,
        # OpenAI parameters
        models: list[str] = ["gpt-3.5-turbo", "gpt-4"],
        model_params: dict | None = None,
        max_cost: float = 1,
        # instructions
        extra_instructions: list[str] | None = None,
        postprocessors: list | None = None,
        # retry rules
        retry: RetryRule = RetryRule(1, 30),
    ):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost: float = 0
        self.max_cost = max_cost
        self.models = models
        self.retry = retry
        if model_params is None:
            model_params = {}
        self.model_params = model_params
        # default temperature to 0, deterministic
        if "temperature" not in model_params:
            model_params["temperature"] = 0

        self.system_messages = []
        if extra_instructions:
            self.system_messages.extend(extra_instructions)

        if postprocessors is None:
            self.postprocessors = self._default_postprocessors
        else:
            self.postprocessors = postprocessors

    def _raw_api_request(
        self,
        model: str,
        messages: list[dict[str, str]],
        response: Response,
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
                f"Total cost {self.total_cost:.2f} exceeds max cost {self.max_cost:.2f}"
            )
        json_mode = (
            {"response_format": "json_object"} if _model_dict[model].json_mode else {}
        )
        start_t = time.time()
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            **self.model_params,
            **json_mode,  # type: ignore
        )
        elapsed = time.time() - start_t
        if completion.usage:
            p_tokens = completion.usage.prompt_tokens
            c_tokens = completion.usage.completion_tokens
        else:
            raise ScrapeghostError("no usage data returned")
        cost = _model_dict[model].cost(c_tokens, p_tokens)
        logger.info(
            "API response",
            duration=elapsed,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            finish_reason=completion.choices[0].finish_reason,
            cost=cost,
        )

        # Note: All modifications to response should be additive, so that
        #       this method can be called multiple times to build a response.
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
        response.data = choice.message.content  # type: ignore
        return response

    def _api_request(self, html: str) -> Response:
        """
        Make an OpenAPI request, with retries and model upgrades.

        * html - the HTML to send to the API
        * response - the Response object to augment
        """
        attempts = 0
        model_index = 0

        response = Response()

        if not html:
            raise ValueError("html parameter cannot be empty")

        while True:
            try:
                # check this within retries, but before API call
                # so that we don't waste an API call but can still
                # upgrade models
                model = self.models[model_index]
                model_data = _model_dict[model]
                # this call is redundant for now since all models have the same
                # tokenizer, but it's here for future-proofing
                tokens = _tokens(model, html)
                if tokens > model_data.max_tokens:
                    raise TooManyTokens(
                        f"HTML is {tokens} tokens, max for {model} is "
                        f"{model_data.max_tokens}"
                    )

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
            except self.retry.retry_errors + (
                TooManyTokens,
                BadStop,
            ) as e:
                logger.warning(
                    "API request failed",
                    exception=str(e),
                    model=model,
                    attempts=attempts,
                )
                if attempts < self.retry.max_retries + 1:
                    if isinstance(e, self.retry.retry_errors):
                        logger.warning("retry", wait=self.retry.retry_wait, model=model)
                        # try again with same model
                        time.sleep(self.retry.retry_wait)
                        continue
                    elif model_index < len(self.models) - 1:
                        # try next model
                        model_index += 1
                        model = self.models[model_index]
                        logger.warning(
                            "retry",
                            wait=self.retry.retry_wait,
                            model=model,
                        )
                        time.sleep(self.retry.retry_wait)
                        continue
                # could not retry for whatever reason
                raise

    def _apply_postprocessors(self, response: Response) -> Response:
        for pp in self.postprocessors:
            logger.debug(
                "postprocessor",
                postprocessor=str(pp),
                data=response.data,
                data_type=type(response.data),
            )
            response = pp(response, self)
        return response

    def request(self, html: str) -> Response:
        """
        Make an OpenAPI request, with retries and model upgrades, and
        postprocessing.
        """
        return self._apply_postprocessors(self._api_request(html))

    def stats(self) -> dict:
        """
        Return stats about the scraper.
        """
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost": self.total_cost,
        }
