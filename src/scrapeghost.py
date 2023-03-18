import json
import openai
import lxml.html
import requests


class InvalidJSONError(Exception):
    pass


class AutoScraper:
    def scrape(
        self,
        url: str,
        *,
        xpath: str | None = None,
        css: str | None = None,
        model: str = "gpt-4",
        input_token_limit: int = 8192,
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
        if xpath and css:
            raise ValueError("Cannot specify both xpath and css")

        html = requests.get(url).text
        print(len(html), "before simplification")

        doc = lxml.html.fromstring(html)

        if xpath:
            html = "\n".join(
                lxml.html.tostring(n, encoding="unicode") for n in doc.xpath(xpath)
            )
        elif css:
            html = "\n".join(
                lxml.html.tostring(n, encoding="unicode") for n in doc.cssselect(css)
            )
        else:
            html = lxml.html.tostring(doc, encoding="unicode")

        if len(html) / 3 > input_token_limit:
            raise ValueError("HTML is too long for the 8k limit")

        print(len(html), "after simplification")

        response = self._handle_html(html, model, max_tokens, temperature)

        try:
            return json.loads(response)
        except json.decoder.JSONDecodeError:
            raise InvalidJSONError(response)

    # allow the class to be called like a function
    __call__ = scrape

    def _handle_html(
        self, html: str, model: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Pass HTML to the OpenAI API and return the response.
        """
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
        return completion.choices[0]["message"]["content"]


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
