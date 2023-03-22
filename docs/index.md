# About

![scrapeghost logo](assets/scrapeghost.png)

`scrapeghost` is an experimental library for scraping websites using OpenAI's GPT.

The library provides a means to scrape structured data from HTML without writing page-specific code.

!!! danger "Important"

    This library is **very experimental** with a rapidly evolving interface.
    No guarantees are made about the stability of the API or the accuracy of the results.

    Additionally, be aware of [the potential costs](openai.md#costs) before using this library.

    **Use at your own risk.**

Currently licensed under [Hippocratic License 3.0](LICENSE.md).   (See [FAQ](faq.md#whats-with-the-license).)

## Quickstart

**Step 1)** Obtain an OpenAI API key (<https://platform.openai.com>) and set an environment variable:

```bash
export OPENAI_API_KEY=sk-...
```

**Step 2)** Install the library however you like:

```bash
pip install scrapeghost
```
or
```bash
poetry add scrapeghost
```

**Step 3)** Instantiate a `SchemaScraper` by defining the shape of the data you wish to extract:

```python
from scrapeghost import SchemaScraper
scrape_legislators = SchemaScraper(
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

!!! note

    There's no pre-defined format for the schema, the GPT models do a good job of figuring out what you want and you can use whatever values you want to provide hints.

**Step 4)** Passing the scraper a URL (or HTML) to the resulting scraper will return a dictionary of the scraped data:

```python
 scrape_legislators("https://www.ilga.gov/house/rep.asp?MemberID=3071")
```
```json
{"name": "Emanuel 'Chris' Welch",
 "url": "https://www.ilga.gov/house/Rep.asp?MemberID=3071",
 "district": "7th", "party": "D", 
 "photo_url": "https://www.ilga.gov/images/members/{5D419B94-66B4-4F3B-86F1-BFF37B3FA55C}.jpg",
   "offices": [
     {"name": "Springfield Office",
      "address": "300 Capitol Building, Springfield, IL 62706",
       "phone": "(217) 782-5350"},
     {"name": "District Office",
      "address": "10055 W. Roosevelt Rd., Suite E, Westchester, IL 60154",
       "phone": "(708) 450-1000"}
   ]}
```

**That's it!**

Read the [tutorial](tutorial.md) for a step-by-step guide to building a scraper.

### Command Line Usage Example

If you've installed the package (e.g. with `pipx`), you can use the `scrapeghost` command line tool to experiment.

```bash
--8<-- "docs/tutorial_code/cli.sh"
```
```json
--8<-- "docs/tutorial_code/cli.log"
```

See [the CLI docs](cli.md) for more details.

## Features

The purpose of this library is to provide a convenient interface for exploring web scraping with GPT.

While the bulk of the work is done by the GPT model, `scrapeghost` provides a number of features to make it easier to use.

**Python-based schema definition** - Define the shape of the data you want to extract as any Python object, with as much or little detail as you want.

**Preprocessing**

* **HTML cleaning** - Remove unnecessary HTML to reduce the size and cost of API requests.
* **CSS and XPath selectors** - Pre-filter HTML by writing a single CSS or XPath selector.
* **Auto-splitting** - Optionally split the HTML into multiple calls to the model, allowing for larger pages to be scraped.

**Postprocessing**

* **JSON validation** - Ensure that the response is valid JSON.  (With the option to kick it back to GPT for fixes if it's not.)
* **Schema validation** - Go a step further, use a [`pydantic`](https://pydantic-docs.helpmanual.io/) schema to validate the response.
* **Hallucination check** - Does the data in the response truly exist on the page?

**Cost Controls**

* Scrapers keep running totals of how many tokens have been sent and received, so costs can be tracked.
* Support for automatic fallbacks (e.g. use cost-saving GPT-3.5-Turbo by default, fall back to GPT-4 if needed.)
* Allows setting a budget and stops the scraper if the budget is exceeded.