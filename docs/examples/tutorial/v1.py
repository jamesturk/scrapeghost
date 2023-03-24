from scrapeghost import SchemaScraper
from pprint import pprint  # pretty print results

url = "https://comedybangbang.fandom.com/wiki/Operation_Golden_Orb"
schema = {
    "title": "str",
    "episode_number": "int",
    "release_date": "str",
}

episode_scraper = SchemaScraper(schema)

pprint(episode_scraper(url))
