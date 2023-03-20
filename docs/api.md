# API Reference

## `SchemaScraper`

The `SchemaScraper` class is the main interface to the API.

An `SchemaScraper` is instantiated with a `schema` argument, which is a dictionary describing the shape of the data you wish to extract.

* `schema` - A dictionary describing the shape of the data you wish to extract.

The following parameters are optional:

* `models` - A list of models to use, in order of preference.  Defaults to `["gpt-3.5-turbo", "gpt-4"]`.  
* `model_params` - A dictionary of parameters to pass to the underlying GPT model.  (See [OpenAI docs](https://platform.openai.com/docs/api-reference/create-completion) for details.)
* `list_mode` - If `True`, the instructions and behavior will be slightly modified to better perform on pages with lists of similar items.
* `extra_instructions` - Additional instructions to pass to the GPT model as a system prompt.
* `split_length` - If set, the scraper will split the page into multiple calls, each of this length. (Only works with `list_mode`, requires passing a `css` or `xpath` selector when scraping.)

### Auto-splitting

It's worth mentioning how `split_length` works because it allows for some interesting possibilities but can also become quite expensive.

If you pass `split_length` to the scraper, it assumes the page is made of multiple similar sections and will try to split the page into multiple calls.  

When you call the scrape function of an auto-splitting enabled scraper, you are required to pass a `css` or `xpath` selector to the function.  The resulting nodes will be combined into chunks no bigger than `split_length` tokens, sent to the API, and then stitched back together.

This seems to work well for long lists of similar items, though whether it is worth the many calls is questionable.

## `scrape`

The `scrape` method of a `SchemaScraper` is used to scrape a page.

```python
scraper = SchemaScraper(schema)
scraper.scrape("https://example.com")
```

* `url_or_html` - The first parameter should be a URL or HTML string to scrape.

You can also pass a CSS or XPath selector as a keyword argument:

* `css` - A CSS selector to use to filter the HTML before sending it to the API.
* `xpath` - An XPath selector to use to filter the HTML before sending it to the API.


It is also possible to call the scraper directly, which is equivalent to calling `scrape`:

```python
scraper = SchemaScraper(schema)
scraper("https://example.com")
# same as writing
scraper.scrape("https://example.com")
```

### Selectors

Pass the `css` or `xpath` arguments to the scraper to use a selector to narrow down the HTML before sending it to the API.

```python
>>> scrape_legislators("https://www.ilga.gov/house/rep.asp?MemberID=3071", xpath="//table[1]")
```

## `PaginatedSchemaScraper`

TODO: document this

## Exceptions

A scrape can raise the following exceptions:

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