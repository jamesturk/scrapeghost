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
* `preprocessors` - *list* - A list of **[preprocessors](#preprocessors)** to run on the HTML before sending it to the API. 
* `split_length` - *int* - If set, the scraper will split the page into multiple calls, each of this length. See [auto-splitting](#auto-splitting) for details.

### Preprocessors

Preprocessors allow you to modify the HTML before it is sent to the API.

Three preprocessors are included by default:

* `CleanHTML` - Cleans the HTML using `lxml.html.clean.Cleaner`.
* `XPath` - Applies an XPath selector to the HTML.
* `CSS` - Applies a CSS selector to the HTML.

Note: `CleanHTML` is always applied as it is part of `SchemaScraper._default_preprocessors`.

You can add your own preprocessors by passing a list of callables to the `preprocessors` parameter.

```python
scraper = SchemaScraper(schema, preprocessors=[CSS("table")])
```

It is also possible to pass preprocessors at scrape time via the `extra_preprocessors` parameter:

```python
scraper = SchemaScraper(schema)
scraper.scrape("https://example.com", extra_preprocessors=[CSS("table")])
```

Implementing your own preprocessor is simple, just create a callable that takes a `lxml.html.HtmlElement` and returns a list of `lxml.html.HtmlElement` objects.  Look at `preprocessors.py` for examples.

### Auto-splitting

It's worth mentioning how `split_length` works because it allows for some interesting possibilities but can also become quite expensive.

If you pass `split_length` to the scraper, it assumes the page is made of multiple similar sections and will try to split the page into multiple calls.  

When you call the scrape function of an auto-splitting enabled scraper, it is important to use a splitting preprocessor like `XPath` or `CSS`.  The resulting nodes will be combined into chunks no bigger than `split_length` tokens, sent to the API, and then stitched back together.

This seems to work well for long lists of similar items, though whether it is worth the many calls is questionable.

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