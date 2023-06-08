# Changelog

## 0.5.1

* Improve type annotations and remove some ignored errors.

## 0.5.0 - 2023-06-06

* Restore `PaginatedSchemaScraper` and add documentation for pagination.
* Documentation improvements.
* Small quality-of-life improvements such as better `pydantic` schema support and
  more useful error messages.

## 0.4.4 - 2023-03-31

* Deactivate `HallucinationCheck` by default, it is overly aggressive and needs more work to be useful without raising false positives.
* Bugfix for postprocessors parameter behavior not overriding defaults.

## 0.4.2 - 2023-03-26

* Fix type bug with JSON nudging.
* Improve `HallucinationCheck` to handle more cases.
* More tests!

## 0.4.1 - 2023-03-24

* Fix bug with HallucinationCheck.

## 0.4.0 - 2023-03-24

* New configurable pre- and post-processing pipelines for customizing behavior.
* Addition of `ScrapeResult` object to hold results of scraping along with metadata.
* Support for `pydantic` models as schemas and for validation.
* "Hallucination" check to ensure that the data in the response truly exists on the page.
* Use post-processing pipeline to "nudge" JSON errors to a better result.
* Now fully type-annotated.
* Another big refactor, separation of API calls and scraping logic.
* Finally, a ghost logo reminiscent of library's [namesake](https://static.wikia.nocookie.net/superheroes/images/4/49/Space_Ghost.jpg/revision/latest/scale-to-width-down/1000?cb=20140111031255).

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
