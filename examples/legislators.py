import sys
from pprint import pprint
from scrapeghost import SchemaScraper, CSS

scrape_legislators = SchemaScraper(
    model="gpt-3.5-turbo",
    schema={
        "name": "string",
        "url": "url",
        "district": "string",
        "party": "string",
        "photo_url": "url",
        "offices": [{"name": "string", "address": "string", "phone": "string"}],
    },
)


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
        pprint(scrape_legislators(url))
    else:
        for url, css in examples:
            pprint(url)
            pprint(scrape_legislators(url, extra_preprocessors=[CSS(css)]))


examples = [
    (
        "https://www.capitol.hawaii.gov/legislature/memberpage.aspx?member=117&year=2023",
        ".contact-box",
    ),
    ("https://legislature.vermont.gov/people/single/2024/37398", "div#main-content"),
    # (
    #     "https://leg.mt.gov/legislator-information/roster/individual/7467",
    #     "div.white:nth-child(1)",
    # ),
    (
        "https://dccouncil.gov/council/ward-4-councilmember-janeese-lewis-george/",
        "article",
    ),
    ("https://www.ncleg.gov/Members/Biography/S/436", None),
    ("https://www.ilga.gov/senate/Senator.asp?GA=103&MemberID=3092", None),
]

if __name__ == "__main__":
    main()
