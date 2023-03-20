# Tutorial

This tutorial will show you how to use `scrapeghost` to build a web scraper without writing page-specific code.

## Prerequisites

### Install `scrapeghost`

You'll need to install `scrapeghost`. You can do this with `pip`, `poetry`, or your favorite Python package manager.

--8<-- "docs/snippets/_apikey.md"

## Writing a Scraper

The goal of our scraper is going to be to get a list of all of the episodes of the podcast [Comedy Bang Bang](https://comedybangbang.fandom.com/wiki/Comedy_Bang_Bang_Wiki).

To do this, we'll need two kinds of scrapers: one to get a list of all of the episodes, and one to get the details of each episode.

### Getting Episode Details

At the time of writing, the most recent episode of Comedy Bang Bang is Episode 800, Operation Golden Orb.

The URL for this episode is <https://comedybangbang.fandom.com/wiki/Operation_Golden_Orb>.

Let's say we want to build a scraper that finds out each episode's title, episode number, and release date.

We can do this by creating a `SchemaScraper` object and passing it a schema.

```python
--8<-- "docs/tutorial_code/v1.py"
```

There is no predefined way to define a schema, but a dictionary resembling the data you want to scrape where the keys are the names of the fields you want to scrape and the values are the types of the fields is a good place to start.

Once you have an instance of `SchemaScraper` you can use it to scrape a specific page by passing it a URL (or HTML if you prefer/need to fetch the data another way).

Running our code gives an error though:

```
scrapeghost.scrapers.TooManyTokens: HTML is 9710 tokens, max for gpt-3.5-turbo is 4096
```

This means that the content length is too long.

### What Are Tokens?

If you haven't used OpenAI's APIs before, you may not be aware of the token limits.  Every request has a limit on the number of tokens it can use. For GPT-4 this is 8,192 tokens. For GPT-3.5-Turbo it is 4,096.  (A token is about three characters.)

You are also billed per token, so even if you're under the limit, fewer tokens means cheaper API calls.

--8<-- "docs/snippets/_cost.md"

So for example, a 4,000 token page that returns 1,000 tokens of JSON will cost $0.01 with GPT-3-Turbo, but $0.18 with GPT-4.

Ideally, we'd only pass the relevant parts of the page to OpenAI. It shouldn't need anything outside of the HTML `<body>`, anything in comments, script tags, etc.

(For more details on how this library interacts with OpenAI's API, see the [OpenAI API](openai.md) page.)

### Preprocessors

To help with all this, `scrapeghost` provides a way to preprocess the HTML before it is sent to OpenAI. This is done by passing a list of preprocessor callables to the `SchemaScraper` constructor.

!!! info

    A `CleanHTML` preprocessor is included by default. This removes HTML comments, script tags, and style tags.


If you visit the page <https://comedybangbang.fandom.com/wiki/Operation_Golden_Orb> viewing the source will reveal that all of the interesting content is in an element `<div id="content" class="page-content">`.

Just as we might if we were writing a real scraper, we'll write a CSS selector to grab this element, `div.page-content` will do.  The `CSS` preprocessor will use this selector to extract the content of the element.


```python hl_lines="1 13 14"
--8<-- "docs/tutorial_code/v2.py"
```

Now, a call to our scraper will only pass the content of the `<div>` to OpenAI. We get the following output:

```log
--8<-- "docs/tutorial_code/v2.log"
```

We can see from the logging output that the content length is much shorter now and we get the data we were hoping for.

All for less than a penny!

!!! tip

    Even when the page fits under the token limit, it is still a good idea to pass a selector to limit the amount of content that OpenAI has to process.

### Enhancing the Schema

That was easy! Let's enhance our schema to include the list of guests as well as requesting the dates in a particular format.

```python
--8<-- "docs/tutorial_code/v3.py"
```

Just two small changes, but now we get the following output:

```log
--8<-- "docs/tutorial_code/v3.log"
```

Let's try this on a different episode, from the beginning of the series.

```python
episode_scraper(
    "https://comedybangbang.fandom.com/wiki/Welcome_to_Comedy_Bang_Bang",
)
```
```log
{'episode_number': 1,
 'guests': [{'name': 'Rob Huebel'},
            {'name': 'Tom Lennon'},
            {'name': 'Doug Benson'}],
 'release_date': '2009-05-01',
 'title': 'Welcome to Comedy Bang Bang'}
```

And there we have it!

### Getting a List of Episodes

Now that we have a scraper that can get the details of each episode, we need a scraper that can get a list of all of the episode URLs.

<https://comedybangbang.fandom.com/wiki/Category:Episodes> has a link to each of the episodes, perhaps we can just scrape that page?

```python
--8<-- "docs/tutorial_code/v4.py"
```
```log
scrapeghost.scrapers.TooManyTokens: HTML is 292918 tokens, max for gpt-3.5-turbo is 4096
```

Yikes, nearly 300k tokens! This is a huge page.

We can try again with a CSS selector, but this time we'll try to get a selector for each individual item.

If you have go this far, you may want to just extract links using `lxml.html` or `BeautifulSoup` instead.

But let's imagine that for some reason you don't want to, perhaps this is a one-off project and even a relatively expensive request is worth it.

`SchemaScraper` has a few options that will help, we'll change our scraper to use `list_mode` and `split_length`.

```python
--8<-- "docs/tutorial_code/v5.py"
```

`list_mode=True` alters the prompt and response format so that instead of returning a single JSON object, it returns a list of objects where each should match your provided `schema`.

We alter the `schema` to just be a single string because we're only interested in the URL.

Finally, we set the `split_length` to 2048. This is the maximum number of tokens that will be passed to OpenAI in a single request.

It's a good idea to set this to about half the token limit, since the response counts against the token limit as well.

This winds up needing to make over twenty requests, but gets the list of episode URLs after a few minutes.

```log
--8<-- "docs/tutorial_code/v5.log"
```

It takes a while, but if you can stick to GPT-3.5-Turbo it's only $0.13.

It isn't perfect, it is quite slow and also adding extra fields to the JSON, but it gets the job done.  It is trivial to combine the output of `episode_list_scraper` with `episode_scraper` to get the metadata for all of the episodes.

See the listing at the very end for the full program.

## Next Steps

This is still very much a proof of concept, but it does work.

I'm interested in ease of use and developer experience, as well as improving the accuracy.  If you want to follow along, [the issues page](https://github.com/jamesturk/scrapeghost/issues) is a good picture of what I'm considering next.

## Putting it all Together

```python
--8<-- "docs/tutorial_code/v6.py"
```