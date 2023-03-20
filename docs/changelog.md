# Changelog

## WIP 

* Rudimentary support for retries when OpenAI returns an error.
* Post-processing pipeline with support for "nudging" errors to a better result.

## 0.3.0 - 2023-03-20

* Add tests, docs, and complete examples!
* Add preprocessors to `SchemaScraper` to allow for uniform interface for cleaning & selecting HTML.
* Use `tiktoken` for accurate token counts.
* New `cost_estimate` utility function.
* Cost is now tracked on a per-scraper basis (see the `total_cost` attribute on `SchemaScraper` objects).
* `SchemaScraper` now takes a `max_cost` parameter to limit the total cost of a scraper.
* Prompt improvements, list mode simplification.

## 0.2.0 - 2023-03-18

* Add list mode, auto-splitting, and pagination support.
* Improve `xpath` and `css` handling.
* Improve prompt for GPT 3.5.
* Make it possible to alter parameters when calling scrape.
* Logging & error handling.
* Command line interface.
* See blog post for details: <https://jamesturk.net/posts/scraping-with-gpt-part-2/>

## 0.1.0 - 2023-03-17

* Initial experiment, see blog post for more: <https://jamesturk.net/posts/scraping-with-gpt-4/>
