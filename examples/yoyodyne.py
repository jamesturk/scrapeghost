"""
This is an example of an auto-paginating scraper using PaginatedSchemaScraper.

The technique used is to modify the schema to have a
"next_page" field, and then scrape in the usual manner.

If "next_page" is populated, the scraper will continue.
"""
import json
from scrapeghost import PaginatedSchemaScraper


schema = {"first_name": "str", "last_name": "str", "position": "str", "url": "url"}
url = "https://scrapple.fly.dev/staff"

scraper = PaginatedSchemaScraper(schema)
data = scraper.scrape_all(url, model="gpt-3.5-turbo")
json.dump(data, open("yoyodyne.json", "w"), indent=2)
