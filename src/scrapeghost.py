import json
import openai
import lxml.html
import requests


class InvalidJSONError(Exception):
    pass


def _recombine(tags, auto_split) -> list[str]:
    """
    Given a list of all matching HTML tags, recombine into HTML chunks
    that can be passed to API.

    Returns list of strings, will always be len()==1 if auto_split is False
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
    ) -> dict:
        """
        Scrape a URL and return a JSON object.

        Args:
            url (str): The URL to scrape.
            css (str, optional): A CSS selector to use to narrow the scope of the scrape. Defaults to None.
            xpath (str, optional): A XPath selector to use to narrow the scope of the scrape. Defaults to None.

        Returns:
            dict: The scraped data in the specified schema.
        """

        def _response_to_json(response: str) -> list | dict:
            print(f"making request now: len={len(response)}")
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
            response = completion.choices[0]["message"]["content"]

            try:
                return json.loads(response)
            except json.decoder.JSONDecodeError:
                raise InvalidJSONError(response)

        if xpath and css:
            raise ValueError("Cannot specify both xpath and css")

        html = requests.get(url).text
        print(len(html), "before simplification")

        doc = lxml.html.fromstring(html)

        if xpath:
            chunks = _recombine(doc.xpath(xpath), auto_split)
        elif css:
            chunks = _recombine(doc.cssselect(css), auto_split)
        else:
            # forced to use single chunk if no selector is specified
            chunks = [lxml.html.tostring(doc, encoding="unicode")]

        print(
            f"broken into {len(chunks)} chunks: "
            + ", ".join(str(len(c)) for c in chunks)
        )

        if len(chunks) == 1:
            return _response_to_json(chunks[0])
        # flatten list of lists
        return [item for chunk in chunks for item in _response_to_json(chunk)]

    # allow the class to be called like a function
    __call__ = scrape

    def _handle_html(
        self, html: str, model: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Pass HTML to the OpenAI API and return the response.
        """


class SchemaScraper(AutoScraper):
    def __init__(self, schema, extra_instructions=None):
        self.system_messages = [
            "When you receive HTML, generate an equivalent JSON object matching this schema: {schema}".format(
                schema=json.dumps(schema)
            ),
        ]
        if extra_instructions:
            self.system_messages.append(extra_instructions)


class LinkExtractor(AutoScraper):
    def __init__(self, extra_instructions=None):
        self.system_messages = [
            'When you receive HTML, extract a list of links matching this schema: [{{"url": "url", "text": "string"}}]',
        ]
        if extra_instructions:
            self.system_messages.append(extra_instructions)
