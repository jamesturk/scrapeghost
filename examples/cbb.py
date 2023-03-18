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
    # model="gpt-4",
    model="gpt-3.5-turbo",
    split_length=6000,
)

# this page has 800 episodes and is far too long for the 8k limit
# so we use css to select only the episode links and auto_split
# to break the HTML into chunks of 6000 characters
try:
    output = scrape_episodes(
        "https://comedybangbang.fandom.com/wiki/Category:Episodes",
        css=".mw-parser-output a[class!='image link-internal']",
    )
except InvalidJSON as e:
    print("Invalid JSON")
    print(e)
    exit(1)

with open("cbb.json", "w") as f:
    json.dump(output, f, indent=1)
