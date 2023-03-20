# API Reference

## `SchemaScraper`

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

### Examples

See the [examples directory](https://github.com/jamesturk/scrapeghost/tree/main/examples) for current usage.

### Configuration

### `scrape`

## Exceptions

A scrape can raise the following exceptions:

### `TooManyTokens`

Raised when the number of tokens being sent exceeds the maximum allowed.

This indicates that the HTML is too large to be processed by the API.

:::{.callout-tip}
Consider using the `css` or `xpath` selectors to reduce the number of tokens being sent, or use the `split_length` parameter to split the request into multiple requests if necessary.
:::

### BadStop

Indicates that OpenAI ran out of space before the stop token was reached.

:::{.callout-tip}
OpenAI considers both the input and the response tokens when determining if the token limit has been exceeded.

If you are using `split_length`, consider decreasing the value to leave more space for responses.
:::

### InvalidJSON

Indicates that the JSON returned by the API is invalid.
