# API Reference

## `SchemaScraper`

The `SchemaScraper` class is the main interface to the API.

It has one required parameter:

* `schema` - A dictionary describing the shape of the data you wish to extract.

And the following optional parameters:

* `models` - *list\[str\]* - A list of models to use, in order of preference.  Defaults to `["gpt-3.5-turbo", "gpt-4"]`.  
* `model_params` - *dict* - A dictionary of parameters to pass to the underlying GPT model.  (See [OpenAI docs](https://platform.openai.com/docs/api-reference/create-completion) for details.)
* `max_cost` -  *float* (dollars) - The maximum total cost of calls made using this scraper. This is set to 1 ($1.00) by default to avoid large unexpected charges.
* `list_mode` - *bool* - If `True`, the instructions and behavior will be slightly modified to better perform on pages with lists of similar items.
* `extra_instructions` - *list\[str\]* - Additional instructions to pass to the GPT model as a system prompt.
* `extra_preprocessors` - *list* - A list of **[preprocessors](#preprocessors)** to run on the HTML before sending it to the API.  This is in addition to the default preprocessors.
* `postprocessors` - *list* - A list of **[postprocessors](#postprocessors)** to run on the results before returning them.  If provided, this will override the default postprocessors.
* `split_length` - *int* - If set, the scraper will split the page into multiple calls, each of this length. See [auto-splitting](#auto-splitting) for details.


## `scrape`

The `scrape` method of a `SchemaScraper` is used to scrape a page.

```python
scraper = SchemaScraper(schema)
scraper.scrape("https://example.com")
```

* `url_or_html` - The first parameter should be a URL or HTML string to scrape.
* `extra_preprocessors` - A list of **[preprocessors](#preprocessors)** to run on the HTML before sending it to the API.


It is also possible to call the scraper directly, which is equivalent to calling `scrape`:

```python
scraper = SchemaScraper(schema)
scraper("https://example.com")
# same as writing
scraper.scrape("https://example.com")
```


## `PaginatedSchemaScraper`

TODO: document this

## Exceptions

The following exceptions can be raised by the scraper:

(all are subclasses of `ScrapeghostError`)

### `MaxCostExceeded`

The maximum cost of the scraper has been exceeded.

Raise the `max_cost` parameter to allow more calls to be made.

### `PreprocessorError`

A preprocessor encountered an error (such as returning an empty list of nodes).

### `TooManyTokens`

Raised when the number of tokens being sent exceeds the maximum allowed.

This indicates that the HTML is too large to be processed by the API.

!!! tip

    Consider using the `css` or `xpath` selectors to reduce the number of tokens being sent, or use the `split_length` parameter to split the request into multiple requests if necessary.

### `BadStop`

Indicates that OpenAI ran out of space before the stop token was reached.

!!! tip

    OpenAI considers both the input and the response tokens when determining if the token limit has been exceeded.

    If you are using `split_length`, consider decreasing the value to leave more space for responses.

### `InvalidJSON`

Indicates that the JSON returned by the API is invalid.