import json
from scrapeghost.scrapers import PaginatedSchemaScraper


schema = {"first_name": "str", "last_name": "str", "position": "str", "url": "url"}
url = "https://scrapple.fly.dev/staff"

scraper = PaginatedSchemaScraper(schema)
resp = scraper.scrape(url)

# the resulting response is a ScrapeResponse object just like any other
# all the results are gathered in resp.data
json.dump(resp.data, open("yoyodyne.json", "w"), indent=2)
