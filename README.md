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

### Basics

The `SchemaScraper` class is the main interface for building automatic scrapers.

To build a scraper, you provide a schema that describes the data you want to collect.

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
```

There's no pre-defined format for the schema, the GPT models do a good job of figuring out what you want and you can use whatever values you want to provide hints.

You can then call the scraper with a URL to scrape:

```python
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

## Command Line Usage

If you've installed the package (e.g. with `pipx`), you can use the `scrapeghost` command line tool to experiment.

```bash
scrapeghost https://www.ncleg.gov/Members/Biography/S/436  \
  --schema "{'first_name': 'str', 'last_name': 'str',
             'photo_url': 'url', 'offices': [] }"  \
  --gpt4

{'first_name': 'Gale',
 'last_name': 'Adcock',
 'photo_url': 'https://www.ncleg.gov/Members/MemberImage/S/436/Low',
 'offices': [
    {'address': '16 West Jones Street, Rm. 1104',
     'city': 'Raleigh', 'state': 'NC', 'zip': '27601',
     'phone': '(919) 715-3036',
     'email': 'Gale.Adcock@ncleg.gov',
     'legislative_assistant': 'Elizabeth Sharpe',
     'legislative_assistant_email': 'Elizabeth.Sharpe@ncleg.gov'
    }
  ]
}
```

```bash
 Usage: scrapeghost [OPTIONS] URL                                                                                               
                                                                                                                                
╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────╮
│ *    url      TEXT  [default: None] [required]                                                    │
╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────╮
│ --xpath                         TEXT     XPath selector to narrow the scrape [default: None]      │
│ --css                           TEXT     CSS selector to narrow the scrape [default: None]        │
│ --schema                        TEXT     Schema to use for scraping [default: None]               │
│ --schema-file                   PATH     Path to schema.json file [default: None]                 │
│ --gpt4             --no-gpt4             Use GPT-4 instead of GPT-3.5-turbo [default: no-gpt4]    │
│ --verbose      -v               INTEGER  Verbosity level 0-2 [default: 0]                         │
│ --help                                   Show this message and exit.                              │
╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Features

### Selectors

The main limitation you'll run into is the token limit. Depending on the model you're using you're limited to 4096 or 8192 tokens per call. Billing is also based on tokens sent and received.

One strategy to deal with this is to provide a CSS or XPath selector to the scraper. This will pre-filter the HTML that is sent to the server, keeping you under the limit and saving you money.

Pass the `css` or `xpath` arguments to the scraper to use a selector:

```python
>>> scrape_legislators("https://www.ilga.gov/house/rep.asp?MemberID=3071", xpath="//table[1]")
```

### SchemaScraper Options

* `model` - The GPT model to use, defaults to `gpt-4`, can also be `gpt-3.5-turbo`.
* `list_mode` - If `True` the scraper will return a list of objects instead of a single object. (Alters the prompts and some behavior.)
* `split_length` - If set, the scraper will split the page into multiple calls, each of this length. (Only works with list_mode, requires passing a `css` or `xpath` selector when scraping.)
* `model_params` - A dictionary of parameters to pass to the underlying GPT model.
* `extra_instructions` - Additional instructions to pass to the GPT model.

### Auto-splitting

It's worth mentioning how `split_length` works because it allows for some interesting possibilities but can also become quite expensive.

If you pass `split_length` to the scraper, it assumes the page is made of multiple similar sections and will try to split the page into multiple calls.  

When you call the scrape function of an auto-splitting enabled scraper, you are required to pass a `css` or `xpath` selector to the function.  The resulting nodes will be combined into chunks no bigger than `split_length` tokens, sent to the API, and then stitched back together.

This seems to work well for long lists of similar items, though whether it is worth the many calls is questionable.

Look at `examples/cbb.py` for an example of a 800+ item page that is split into many calls.

## Changelog

### 0.2.0 - 2021-03-18

* Add list mode, auto-splitting, and pagination support.
* Improve `xpath` and `css` handling.
* Improve prompt for GPT 3.5.
* Make it possible to alter parameters when calling scrape.
* Logging & error handling.
* Command line interface.
* See blog post for details: <https://jamesturk.net/posts/scraping-with-gpt-4-part-2/>

### 0.1.0 - 2021-03-17

* Initial experiment, see blog post for more: <https://jamesturk.net/posts/scraping-with-gpt-4/>
