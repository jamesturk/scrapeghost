import json
import time
import openai
from .utils import logger, _tostr, _chunk_tags, _parse_url_or_html, _select_tags


class BadStop(Exception):
    pass


class InvalidJSON(Exception):
    pass


class SchemaScraper:
    def __init__(
        self,
        schema: dict,
        *,
        models: str = ["gpt-3.5-turbo", "gpt-4"],
        model_params: dict | None = None,
        list_mode: bool = False,
        extra_instructions: str = "",
        split_length: int = 0,
    ):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.models = models
        if model_params is None:
            model_params = {}
        self.model_params = model_params
        # default temperature to 0, deterministic
        if "temperature" not in model_params:
            model_params["temperature"] = 0

        self.split_length = split_length

        if list_mode:
            self.system_messages = [
                "For the given HTML, convert to a list of JSON objects matching this schema: {schema}".format(
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
            self.system_messages.append(extra_instructions)

    def _api_request(self, html: str, model: str) -> list | dict:
        """
        Given HTML, return JSON using OpenAI API
        """
        if not html:
            raise ValueError("html parameter cannot be empty")
        logger.info(
            "API request",
            model=model,
            length=len(html),
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
        logger.info(
            "API response",
            duration=time.time() - start_t,
            prompt_tokens=completion.usage.prompt_tokens,
            completion_tokens=completion.usage.completion_tokens,
            finish_reason=completion.choices[0].finish_reason,
        )
        self.total_prompt_tokens += completion.usage.prompt_tokens
        self.total_completion_tokens += completion.usage.completion_tokens
        choice = completion.choices[0]
        if choice.finish_reason != "stop":
            raise BadStop(
                f"OpenAI did not stop: {choice.finish_reason} "
                f"(prompt_tokens={completion.usage.prompt_tokens}, "
                f"completion_tokens={completion.usage.completion_tokens})"
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

    def scrape(
        self,
        url_or_html: str,
        *,
        xpath: str | None = None,
        css: str | None = None,
    ) -> dict | list:
        """
        Scrape a URL and return a list or dict.

        Args:
            url: The URL to scrape.
            css: A CSS selector to use to narrow the scope of the scrape.
                 Defaults to None.
            xpath: A XPath selector to use to narrow the scope of the scrape.
                 Defaults to None.
            max_tokens: The maximum number of tokens to use. Defaults to 2048.

        Returns:
            dict | list: The scraped data in the specified schema.
        """
        doc = _parse_url_or_html(url_or_html)
        tags = _select_tags(doc, xpath, css)
        if self.split_length:
            chunks = _chunk_tags(tags, self.split_length)
            # flatten list of lists
            return [item for chunk in chunks for item in self._html_to_json(chunk)]

        else:
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
