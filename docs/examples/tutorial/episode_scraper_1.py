from scrapeghost import SchemaScraper
from pprint import pprint

url = "https://comedybangbang.fandom.com/wiki/Operation_Golden_Orb"
schema = {
    "title": "str",
    "episode_number": "int",
    "release_date": "str",
}

episode_scraper = SchemaScraper(schema)

response = episode_scraper(url)
pprint(response.data)
print(f"Total Cost: ${response.total_cost:.3f}")
