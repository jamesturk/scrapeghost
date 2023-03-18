import json
from scrapeghost import SchemaScraper

scrape_episodes = SchemaScraper(
    schema={
        "title": "string",
        "url": "url",
    },
    extra_instructions="Return one object per episode link, limit to one link.",
)

# this page has 800 episodes and is currently too long for the 8k limit
output = scrape_episodes(
    "https://comedybangbang.fandom.com/wiki/Category:Episodes",
    css=".mw-parser-output a[class!='image link-internal']",
    auto_split=3000,
    model="gpt-3.5-turbo",
    # model="gpt-4",
)
with open("cbb.json", "w") as f:
    json.dump(output, f, indent=1)
