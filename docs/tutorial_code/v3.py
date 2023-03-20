from scrapeghost import SchemaScraper, CSS
from pprint import pprint

url = "https://comedybangbang.fandom.com/wiki/Operation_Golden_Orb"
schema = {
    "title": "str",
    "episode_number": "int",
    "release_date": "YYYY-MM-DD",
    "guests": [{"name": "str"}],
}

episode_scraper = SchemaScraper(
    schema,
    preprocessors=[CSS("div.page-content")],
)

pprint(episode_scraper(url))
