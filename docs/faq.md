# FAQ 

*Mostly questions I've been frequently asking myself.*

## Is this practical? Or just a toy?

When I started the project, I think I assumed it was a toy. But I've been surprised by the results.

After my initial GPT-4 experiments, [Simon Willison asked](https://mastodon.social/@simon@simonwillison.net/110042216119791967) how well it'd work on GPT-3.5-turbo. I hadn't realized the enormous price difference, and without switching to 3.5-turbo, I'd probably have decided it was too expensive to be practical.

Once I realized 3.5-turbo was an option, I was able to spend a lot more time tinkering with the prompt and token reduction.  It also got me thinking more about what kind of tooling you'd want around something like this if you were going to actually use it.

It's certainly started to feel more practical now, I'm not sure I'd call it a toy anymore.

## Why would I use this instead of a traditional scraper?

It is definitely great for quick prototypes. With the CLI tool, you can try a scrape in a *single command*.
This means you don't need to sink a bunch of time into deciding if it's worth it or not.

Or, imagine a scraper that needs to run infrequently on a page that is likely to break in subtle ways between scrapes.
A CSS/XPath-based scraper will often be broken in small ways between the first run and another run months later, there's a decent chance that those changes won't break a GPT-based scraper.

It is also quite good at dealing with unstructured text. A list of items in a sentence can be hard to handle with a traditional scraper, but GPT handles many of these cases without much fuss.

## What are the disadvantages?

* It is terrible at pages that are large lists (like a directory), they need to be broken into multiple chunks and the API calls can be quite expensive in terms of time and money.
* It is quite opaque.  When it fails, it can be hard to tell why.
* If the page is dynamic, this approach won't work at all.  It requires all of the content to be available in the HTML.
* It is *slow*.  A single request can take up to a minute.
* Right now, it only works with OpenAI, that means you'll be dependent on their pricing and availability. It also means
you need to be comfortable sending your data to a third party.


## Why not use a different model?

I'm open to trying other models if you have suggestions.  (See <https://github.com/jamesturk/scrapeghost/issues/18>)

## What can I do if a page is too big?

Try the following:

1. Provide a CSS or XPath selector to limit the scope of the page.

2. Pre-process the HTML. Trim tags or entire sections you don't need.

3. Finally, you can use the `auto_split_length` parameter to split the page into smaller chunks.  This only works for list-type pages, and requires a good choice of selector to split the page up.

## Why not ask the scraper to write CSS / XPath selectors?

While it'd seem like this would perform better, there are a few practical challenges standing in the way right now.

* Writing a robust CSS/XPath selector that'd run against a whole set of pages would require passing a lot of context to the model. The token limit is already the major limitation.
* The current solution does not require any changes when a page changes.  A selector-based model would require retraining every time a page changes as well as a means to detect such changes.
* For some data, selectors alone are not enough. The current model can easily extract all of the addresses from a page and break them into city/state/etc. A selector-based model would not be able to do this.

I do think there is room for hybrid approaches, and I plan to continue to explore them.

## Does the model "hallucinate" data?

It is possible, but in practice hasn't been observed as a major problem yet.

Because the [*temperature*](https://platform.openai.com/docs/api-reference/completions) is zero, the output is fully deterministic and seems less likely to hallucinate data.

It is definitely possible however, and future versions of this tool will allow for automated error checking (and possibly correction).

## How much did you spend developing this?

So far, about $25 on API calls, switching to GPT-3.5 as the default made a big difference.

My most expensive call was a paginated GPT-4 call that cost $2.20.  I decided to add the cost-limiting features after that.

## What's with the license?

I'm still working on figuring this out.

For now, if you're working in a commercial setting and the license scares you away, that's fine.

If you really want to, you can contact me and we can work something out.