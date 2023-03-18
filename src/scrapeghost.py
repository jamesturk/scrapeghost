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

    def scrape(self, url: str, hint: str | None = None) -> dict:
        """
        Scrape a URL and return a JSON object.

        Args:
            url (str): The URL to scrape.
            hint (str, optional): A CSS selector to use to narrow the scope of the scrape. Defaults to None.

        Returns:
            dict: The scraped data in the specified schema.
        """
        html = requests.get(url).text
        if hint:
            html = lxml.html.tostring(
                lxml.html.fromstring(html).cssselect(hint)[0], encoding="unicode"
            )

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
