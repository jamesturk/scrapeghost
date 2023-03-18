import json
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
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def scrape(
        self,
        url: str,
        *,
        xpath: str | None = None,
        css: str | None = None,
        auto_split: int = 0,
        model: str = "gpt-4",
        max_tokens: int = 2048,
        temperature: float = 0,
    ) -> dict | list:
        """
        Scrape a URL and return a list or dict.

        Args:
            url: The URL to scrape.
            css: A CSS selector to use to narrow the scope of the scrape. Defaults to None.
            xpath: A XPath selector to use to narrow the scope of the scrape. Defaults to None.
            auto_split: If set, split the HTML into chunks of this size. Defaults to 0.
            model: The OpenAI model to use. Defaults to "gpt-4".
            max_tokens: The maximum number of tokens to use. Defaults to 2048.
            temperature: The temperature to use. Defaults to 0.

        Returns:
            dict | list: The scraped data in the specified schema.
        """

        def _html_to_json(html: str) -> list | dict:
            logger.info(
                "API request",
                model=model,
                # html=html,
                length=len(html),
                messages=self.system_messages,
            )
            completion = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": msg} for msg in self.system_messages
                ]
                + [
                    {"role": "user", "content": html},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            logger.info(
                "API response",
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

        if xpath and css:
            raise ValueError("Cannot specify both xpath and css parameters")

        html = requests.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        logger.info("got HTML", length=len(html))

        if xpath:
            chunks = _chunk_tags(doc.xpath(xpath), auto_split)
        elif css:
            chunks = _chunk_tags(doc.cssselect(css), auto_split)
        else:
            # single chunk if no selector is specified
            return _html_to_json(lxml.html.tostring(doc, encoding="unicode"))

        logger.info(
            "broken into chunks",
            num=len(chunks),
            sizes=", ".join(str(len(c)) for c in chunks),
        )
        # flatten list of lists
        return [item for chunk in chunks for item in _html_to_json(chunk)]

    # allow the class to be called like a function
    __call__ = scrape


class SchemaScraper(AutoScraper):
    def __init__(
        self,
        schema: dict,
        *,
        extra_instructions: str | None = None,
        list_mode: bool = False,
    ):
        super().__init__()
        if list_mode:
            self.system_messages = [
                "For the given HTML, convert to a list of JSON objects matching this schema: {schema}".format(
                    schema=json.dumps(schema)
                ),
                "Responses should be a list of valid JSON objects, with no other text."
                "Never truncate the JSON with an ellipsis.",
            ]
        else:
            self.system_messages = [
                "For the given HTML, convert to a JSON object matching this schema: {schema}".format(
                    schema=json.dumps(schema)
                ),
                "Responses should be a valid JSON object, with no other text.",
                "Never truncate the JSON with an ellipsis.",
            ]
        if extra_instructions:
            self.system_messages.append(extra_instructions)


class PaginatedSchemaScraper(SchemaScraper):
    def __init__(self, schema, extra_instructions=None):
        schema = {
            "results": schema,
            "next_link": "url",
        }
        super().__init__(schema, extra_instructions=extra_instructions, list_mode=False)

    def scrape_all(self, url, **kwargs):
        results = []
        while url:
            logger.info("scraping page", url=url)
            page = self.scrape(url, **kwargs)
            print(page)
            results.extend(page["results"])
            url = page["next_link"]
        return results


class LinkExtractor(AutoScraper):
    def __init__(self, extra_instructions=None):
        super().__init__()
        self.system_messages = [
            'When you receive HTML, extract a list of links matching this schema: [{{"url": "url", "text": "string"}}]',
        ]
        if extra_instructions:
            self.system_messages.append(extra_instructions)
