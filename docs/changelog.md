# Changelog

## 0.3.0 - WIP

* Added tests, docs, and complete examples!
* Use `tiktoken` for tokenization instead of guessing.
* Cost is now tracked on a per-scraper basis (see the `total_cost` attribute on `SchemaScraper` objects).
* `SchemaScraper` now takes a `max_cost` parameter to limit the total cost of a scraper.
* New `estimate_cost` utility function.
* list mode prompt improvements

## 0.2.0 - 2021-03-18

* Add list mode, auto-splitting, and pagination support.
* Improve `xpath` and `css` handling.
* Improve prompt for GPT 3.5.
* Make it possible to alter parameters when calling scrape.
* Logging & error handling.
* Command line interface.
* See blog post for details: <https://jamesturk.net/posts/scraping-with-gpt-part-2/>

## 0.1.0 - 2021-03-17

* Initial experiment, see blog post for more: <https://jamesturk.net/posts/scraping-with-gpt-4/>
