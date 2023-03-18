# scrapeghost

An experiment in using GPT-4 to scrape websites.

## Usage

Use SchemaScraper to create scrapers for pages:

```bash
>>> from scrapeghost import SchemaScraper
>>> scrape_legislators = SchemaScraper(
    schema={
        "name": "string",
        "url": "url",
        "district": "string",
        "party": "string",
        "photo_url": "url",
        "offices": [{"name": "string", "address": "string", "phone": "string"}],
    }
)
>>> scrape_legislators("https://www.ilga.gov/house/rep.asp?MemberID=3071")
{'name': 'Emanuel "Chris" Welch', 'url': 'https://www.ilga.gov/house/Rep.asp?MemberID=3071', 'district': '7th', 'party': 'D', 'photo_url': 'https://www.ilga.gov/images/members/{5D419B94-66B4-4F3B-86F1-BFF37B3FA55C}.jpg', 'offices': [{'name': 'Springfield Office', 'address': '300 Capitol Building, Springfield, IL 62706', 'phone': '(217) 782-5350'}, {'name': 'District Office', 'address': '10055 W. Roosevelt Rd., Suite E, Westchester, IL 60154', 'phone': '(708) 450-1000'}]}
```

That's it.

See the blog post for more: <https://jamesturk.net/posts/scraping-with-gpt4/>
