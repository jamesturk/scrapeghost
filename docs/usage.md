# Usage

## Request Data Flow

Since most of the work is done by the API, the primary purpose of `scrapeghost` is to make it easier to pass HTML and get valid output.

To this end, it is useful to understand the data flow:

1. The page HTML is passed through any [preprocessors](#preprocessors).

    a. The `CleanHTML` preprocessor removes unnecessary tags and attributes.  (This is done by default.)

    b. If an `XPath` or `CSS` preprocessor is used, the results are selected and re-combined into a single HTML string.

    c. Custom preprocessors can also execute here.

2. The HTML and schema are sent to the LLM with instructions to extract.

3. The results are passed through any [postprocessors](#postprocessors).

    a. The `JSONPostprocessor` converts the results to JSON.  (This is done by default.) If the results are not valid JSON, a second (much smaller) request can be made to ask it to fix the JSON.

    b. Custom postprocessors can also execute here.

You can modify nearly any part of the process to suit your needs.  (See [Customization](#customization) for more details.)

### Auto-splitting

While the flow above covers most cases, there is one special case that is worth mentioning.

If you set the `auto_split_length` parameter to a positive integer, the HTML will be split into multiple requests where each
request aims to be no larger than `auto_split_length` tokens.

!!! warning

    In **list mode**, a single call can make many requests. Keep an eye on the `max_cost` parameter if you're using this.

    While this seems to work well for long lists of similar items, the question of it is worth the time and money is up to you, writing a bit of code is probably the better option in most cases.

Instead of recombining the results of the `XPath` or `CSS` preprocessor, the results are instead chunked into smaller pieces (<= `auto_split_length`) and sent to the API separately.

The instructions are also modified slightly, indicating that your schema is for a list of similar items.

## Customization

### HTTP Requests

Instead of providing mechanisms to customize the HTTP request made by the library (e.g. to use caching, or make a `POST`), you can simply pass already retrieved HTML to the `scrape` method.

This means you can use any HTTP library you want to retrieve the HTML.

### Preprocessors

Preprocessors allow you to modify the HTML before it is sent to the API.

Three preprocessors are included by default:

* `CleanHTML` - Cleans the HTML using `lxml.html.clean.Cleaner`.
* `XPath` - Applies an XPath selector to the HTML.
* `CSS` - Applies a CSS selector to the HTML.

!!! note

    `CleanHTML` is always applied first, as it is part of the default preprocessors list.

You can add your own preprocessors by passing a list of callables to the `extra_preprocessors` parameter of `SchemaScraper`.

```python
scraper = SchemaScraper(schema, extra_preprocessors=[CSS("table")])
```

It is also possible to pass preprocessors at scrape time:

```python
scraper = SchemaScraper(schema)
scraper.scrape("https://example.com", extra_preprocessors=[CSS("table")])
```

Implementing your own preprocessor is simple, just create a callable that takes a `lxml.html.HtmlElement` and returns a list of one or more `lxml.html.HtmlElement` objects.  Look at `preprocessors.py` for examples.

### Altering the Instructions to GPT

Right now you can pass additional instructions to GPT by passing a list of strings to the `extra_instructions` parameter of `SchemaScraper`.

You can also pass `model_params` to pass additional arguments to the API.

```python
schema = {"name": "str", "committees": [], "bio": "str"}
scraper = SchemaScraper(
    schema,
    models=["gpt-4"],
    extra_instructions=["Put the legislator's bio in the 'bio' field. Summarize it so that it is no longer than 3 sentences."],
)
scraper.scrape("https://norton.house.gov/about/full-biography")
```
```json
{'name': 'Representative Eleanor Holmes Norton',
 'committees': [
    'House Subcommittee on Highways and Transit',
    'Committee on Oversight and Reform',
    'Committee on Transportation and Infrastructure'
    ],
  'bio': 'Congresswoman Eleanor Holmes Norton has been serving as the congresswoman for the District of Columbia since 1991. She is the Chair of the House Subcommittee on Highways and Transit and serves on two committees: the Committee on Oversight and Reform and the Committee on Transportation and Infrastructure. Before her congressional service, President Jimmy Carter appointed her to serve as the first woman to chair the U.S. Equal Employment Opportunity Commission.'}
```

These instructions can be useful for refining the results, but they are not required.

### Altering the API / Model 

See <https://github.com/jamesturk/scrapeghost/issues/18>

### Postprocessors

Postprocessors take the results of the API call and modify them before returning them to the user.

The default is to just use `JSONPostprocessor` which converts the results to JSON.

Postprocessors can be overridden by passing a list of callables to the `postprocessors` parameter of `SchemaScraper`.