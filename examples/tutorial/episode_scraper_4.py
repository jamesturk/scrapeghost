from scrapeghost import SchemaScraper, CSS
from pprint import pprint

url = "https://www.earwolf.com/episode/operation-golden-orb/"
schema = {
    "title": "str",
    "episode_number": "int",
    "release_date": "YYYY-MM-DD",
    "guests": [{"name": "str"}],
}

episode_scraper = SchemaScraper(
    schema,
    extra_preprocessors=[CSS(".hero-episode")],
)

response = episode_scraper(url)
pprint(response.data)
print(f"Total Cost: ${response.total_cost:.3f}")
