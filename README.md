# scrapeghost

`scrapeghost` is an experimental library for scraping websites using OpenAI's GPT.

Source: [https://github.com/jamesturk/scrapeghost](https://github.com/jamesturk/scrapeghost)

Documentation: [https://jamesturk.github.io/scrapeghost/](https://jamesturk.github.io/scrapeghost/)

Issues: [https://github.com/jamesturk/scrapeghost/issues](https://github.com/jamesturk/scrapeghost/issues)

[![PyPI badge](https://badge.fury.io/py/scrapeghost.svg)](https://badge.fury.io/py/scrapeghost)
[![Test badge](https://github.com/jamesturk/scrapeghost/workflows/Test%20&%20Lint/badge.svg)](https://github.com/jamesturk/scrapeghost/actions?query=workflow%3A%22Test+%26+Lint%22)

**Use at your own risk. This library makes considerably expensive calls ($0.36 for a GPT-4 call on a moderately sized page.) Cost estimates are based on the [OpenAI pricing page](https://beta.openai.com/pricing) and not guaranteed to be accurate.**

![](screenshot.png)

## Features

The purpose of this library is to provide a convenient interface for using GPT for the purpose of web scraping.

**Python-based schema definition** - Define the shape of the data you want to extract as any Python object.

* Future versions will support optional validation that the response matches the schema.

**Token Reduction** - Fewer tokens means lower costs, faster responses, and staying under the API's token limits.

* **Automatic HTML cleaning** - Remove unnecessary HTML tags and attributes to reduce the size of the HTML sent to the model.
* **CSS and XPath selectors** - Pre-filter the HTML to send to the model by writing a single CSS or XPath selector.
* **Auto-splitting** - Optionally split the HTML into multiple calls to the model, each of a specified length.

**Cost Controls** - Scrapers keep running totals of how many tokens have been sent and received, so costs can be tracked.

* Future versions will allow setting a budget and stopping the scraper if the budget is exceeded.

**Model Options** - Works with GPT-3.5-Turbo or GPT 4, and allows passing additional parameters to the model to customize behavior.

* Support for automatic fallbacks (e.g. use cost-saving GPT-3.5-Turbo by default, fall back to GPT-4 if needed.)

**Error Handling & Logging** - Detailed logging and error handling to help debug issues.
