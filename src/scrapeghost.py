import json
import time
import openai
import lxml.html
import requests
import structlog


class BadStop(Exception):
    pass


class InvalidJSON(Exception):
    pass


logger = structlog.get_logger("scrapeghost")


def _chunk_tags(tags: list, auto_split: int) -> list[str]:
    """
    Given a list of all matching HTML tags, recombine into HTML chunks
    that can be passed to API.

    Returns list of strings, will always be len()==1 if auto_split is 0
    """
    if not auto_split:
        return ["\n".join(lxml.html.tostring(n, encoding="unicode") for n in tags)]

    # dumb hack to send input in chunks
    pieces = []
    cur_piece = ""
    cur_piece_len = 0
    for tag in tags:
        tag_html = lxml.html.tostring(tag, encoding="unicode")
        tag_len = len(tag_html)
        if cur_piece_len + tag_len > auto_split:
            pieces.append(cur_piece)
            cur_piece = ""
            cur_piece_len = 0
        cur_piece += tag_html
        cur_piece_len += tag_len

    pieces.append(cur_piece)
    return pieces


class AutoScraper:
    def __init__(
        self,
        model: str = "gpt-4",
        model_params: dict | None = None,
        extra_instructions: str = "",
    ):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.model = model
        if model_params is None:
            model_params = {}
        self.model_params = model_params
        # default temperature to 0, deterministic
        if "temperature" not in model_params:
            model_params["temperature"] = 0
        self.extra_instructions = extra_instructions

    def _html_to_json(self, html: str) -> list | dict:
        logger.info(
            "API request",
            model=self.model,
            length=len(html),
            messages=self.system_messages,
        )
        start_t = time.time()
        completion = openai.ChatCompletion.create(
            model=self.model,
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

    def _parse_url_or_html(self, url_or_html: str) -> str:
        # coerce to HTML
        orig_url = None
        if url_or_html.startswith("http"):
            orig_url = url_or_html
            url_or_html = requests.get(url_or_html).text
        logger.info("got HTML", length=len(url_or_html), url=orig_url)
        doc = lxml.html.fromstring(url_or_html)
        if orig_url:
            doc.make_links_absolute(orig_url)
        return doc

    def scrape(
        self,
        url_or_html: str,
        *,
        xpath: str | None = None,
        css: str | None = None,
        auto_split: int = 0,
    ) -> dict | list:
        """
        Scrape a URL and return a list or dict.

        Args:
            url: The URL to scrape.
            css: A CSS selector to use to narrow the scope of the scrape.
                 Defaults to None.
            xpath: A XPath selector to use to narrow the scope of the scrape.
                 Defaults to None.
            auto_split: If set, split the HTML into chunks of this size. Defaults to 0.
            model: The OpenAI model to use. Defaults to "gpt-4".
            max_tokens: The maximum number of tokens to use. Defaults to 2048.

        Returns:
            dict | list: The scraped data in the specified schema.
        """

        if xpath and css:
            raise ValueError("Cannot specify both xpath and css parameters")

        doc = self._parse_url_or_html(url_or_html)

        if xpath:
            chunks = _chunk_tags(doc.xpath(xpath), auto_split)
        elif css:
            chunks = _chunk_tags(doc.cssselect(css), auto_split)
        else:
            # single chunk if no selector is specified
            return self._html_to_json(lxml.html.tostring(doc, encoding="unicode"))

        logger.info(
            "broken into chunks",
            num=len(chunks),
            sizes=", ".join(str(len(c)) for c in chunks),
        )
        # flatten list of lists
        return [item for chunk in chunks for item in self._html_to_json(chunk)]

    # allow the class to be called like a function
    __call__ = scrape


class SchemaScraper(AutoScraper):
    def __init__(
        self,
        schema: dict,
        *,
        list_mode: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if list_mode:
            self.system_messages = [
                "For the given HTML, convert to a list of JSON objects matching this schema: {schema}".format(
                    schema=json.dumps(schema)
                ),
            ]
        else:
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
        if self.extra_instructions:
            self.system_messages.append(self.extra_instructions)


class PaginatedSchemaScraper(SchemaScraper):
    def __init__(self, schema, **kwargs):
        schema = {
            "results": schema,
            "next_link": "url",
        }
        super().__init__(schema, list_mode=False, **kwargs)
        self.system_messages.append("If there is no next page, set next_link to null.")

    def scrape_all(self, url, **kwargs):
        results = []
        seen_urls = set()
        while url:
            logger.info("page", url=url)
            page = self.scrape(url, **kwargs)
            logger.info(
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
