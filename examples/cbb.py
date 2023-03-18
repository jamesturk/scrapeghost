import json
from scrapeghost import SchemaScraper, InvalidJSON

scrape_episodes = SchemaScraper(
    schema={
        "title": "string",
        "url": "url",
    },
)

# this page has 800 episodes and is currently too long for the 8k limit
try:
    output = scrape_episodes(
        "https://comedybangbang.fandom.com/wiki/Category:Episodes",
        css=".mw-parser-output a[class!='image link-internal']",
        auto_split=4000,
        #        model="gpt-3.5-turbo",
        model="gpt-4",
    )
except InvalidJSON as e:
    print(e)
    exit(1)

with open("cbb.json", "w") as f:
    json.dump(output, f, indent=1)
