"""
Scrape Illinois legislators from https://www.ilga.gov/senate/default.asp
"""
import sys
import json
import lxml.html
import requests
from scrapeghost import SchemaScraper, CSS


def get_urls():
    # this page is currently too long for the 8k limit, even with hints
    html = requests.get("https://www.ilga.gov/senate/default.asp").text
    doc = lxml.html.fromstring(html)
    doc.make_links_absolute("https://www.ilga.gov/senate/")
    return [
        a.attrib["href"]
        for a in doc.cssselect("a")
        if "Senator.asp" in a.attrib["href"]
    ]


scrape_legislators = SchemaScraper(
    schema={
        "name": "string",
        "url": "url",
        "district": "string",
        "party": "string",
        "offices": [{"name": "string", "address": "string", "phone": "string"}],
    },
    models=["gpt-4"],
    extra_preprocessors=[
        CSS("table"),
    ],
)


def main():
    # to avoid high bills
    LIMIT = 10

    if len(sys.argv) > 1:
        urls = sys.argv[1:]
    else:
        urls = get_urls()

    legislators = []
    for url in urls:
        legislator = scrape_legislators(url)
        legislator["url"] = url
        legislators.append(legislator)

        if len(legislators) >= LIMIT:
            break

    json.dump(legislators, open("il_legislators.json", "w"), indent=2)


if __name__ == "__main__":
    main()
