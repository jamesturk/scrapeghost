import json
import openai
import lxml.html
import requests


class InvalidJSONError(Exception):
    pass


class AutoScraper:
    def __init__(self):
        self.max_tokens = 2048
        self.temperature = 0
        self.system_messages = []

    def scrape(
        self, url: str, xpath: str | None = None, css: str | None = None
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

        print(len(html), "after simplification")

        if len(html) > 8192:
            print(html)
            raise ValueError("HTML is too long for the 8k limit")

        response = self.handle_html(html)
        try:
            return json.loads(response)
        except json.decoder.JSONDecodeError:
            raise InvalidJSONError(response)

    # allow the class to be called like a function
    __call__ = scrape

    def handle_html(self, html: str) -> str:
        """
        Pass HTML to the OpenAI API and return the response.
        """
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": msg} for msg in self.system_messages
            ]
            + [
                {"role": "user", "content": html},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return completion.choices[0]["message"]["content"]


class SchemaScraper(AutoScraper):
    def __init__(self, schema):
        super().__init__()
        self.schema = schema
        self.system_messages = [
            "When you receive HTML, generate an equivalent JSON object matching this schema: {schema}".format(
                schema=json.dumps(schema)
            ),
        ]


class LinkExtractor(AutoScraper):
    def __init__(self, specific_instructions: str | None = None):
        super().__init__()
        self.system_messages = [
            'When you receive HTML, extract a list of links matching this schema: [{{"url": "url", "text": "string"}}]',
        ]
        if specific_instructions:
            self.system_messages.append(specific_instructions)
