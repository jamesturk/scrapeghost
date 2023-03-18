# scrapeghost

An experiment in using GPT-4 to scrape websites.

**Caution: Use at your own risk, a single call can cost somewhere around $0.36 on larger pages at current rates.**

See the [examples directory](https://github.com/jamesturk/scrapeghost/tree/main/examples) for current usage.

## License

Currently licensed under Hippocratic License 3.0, see [LICENSE.md](LICENSE.md) for details.

## Usage

You will need an OpenAI API key with access to the GPT-4 API.  Configure those as you otherwise would via the `openai` library.

```python
import openai
openai.organization = os.getenv("OPENAI_API_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")
```

Then, use `SchemaScraper` to create scrapers for pages by defining the shape of the data you want to extract:

```python
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
{'name': 'Emanuel "Chris" Welch',
 'url': 'https://www.ilga.gov/house/Rep.asp?MemberID=3071',
 'district': '7th', 'party': 'D', 
 'photo_url': 'https://www.ilga.gov/images/members/{5D419B94-66B4-4F3B-86F1-BFF37B3FA55C}.jpg',
  'offices': [
    {'name': 'Springfield Office', 'address': '300 Capitol Building, Springfield, IL 62706', 'phone': '(217) 782-5350'},
    {'name': 'District Office', 'address': '10055 W. Roosevelt Rd., Suite E, Westchester, IL 60154', 'phone': '(708) 450-1000'}
   ]}
```

**That's it.**

You can also provide a selector to the scraper to help it find the right data, this is useful for managing the total number of tokens sent since the CSS/XPath selector will be executed before sending the data to the API:

```python
>>> scrape_legislators("https://www.ilga.gov/house/rep.asp?MemberID=3071", xpath="//table[1]")
```

## Changelog

### 0.2.0 - WIP

* Improve `xpath` and `css` handling.
* Improve prompt for GPT 3.5.
* Make it possible to alter parameters when calling scrape.
* Add support for splitting large pages into multiple calls.
* New examples for splitting and pagination.

### 0.1.0 - 2021-03-17

* Initial experiment, see blog post for more: <https://jamesturk.net/posts/scraping-with-gpt-4/>
