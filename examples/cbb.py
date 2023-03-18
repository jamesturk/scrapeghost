"""
This is an example of a scraper that needs to handle
an enormous HTML page.  (800 episodes with tons of extra HTML)

We need every trick in the book:

* list_mode helps ensure proper JSON output
* auto_split helps ensure we don't exceed the token limit
* css helps shrink the page as small as possible with a well-chosen
  selector to get the minimal HTML
"""
import json
from scrapeghost import SchemaScraper, InvalidJSON

scrape_episodes = SchemaScraper(
    schema={
        "title": "string",
        "url": "url",
    },
    list_mode=True,
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
