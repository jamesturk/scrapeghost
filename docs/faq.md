# FAQ 

## Is this practical?

When I started this project, I really didn't think it would be. I was aiming at a fun proof of concept, but I've been surprised by the results.

Time will tell if this is a practical tool, but I'm somewhat hopeful now.

## Why not use a different model?

This was a toy project, not an attempt to build a production system.  I'm open to trying other models if you have suggestions.

## What about pages where the data is loaded dynamically?

This won't work for those out of the box.  It should be possible to use something like [selenium](https://selenium-python.readthedocs.io/) to load the page and then pass the rendered HTML to `scrapeghost`.

## What if a page is too big?

Try the following:

1. Provide a CSS or XPath selector to limit the scope of the page.

2. Pre-process the HTML. Trim tags or entire sections you don't need.

3. Finally, you can use the `split_length` parameter to split the page into smaller chunks.  This only works for list-type pages, and requires a good choice of selector to split the page up.

## Why not ask the scraper to write CSS / XPath selectors?

While it'd seem like this would perform better, there are a few practical challenges standing in the way right now.

* Writing a robust CSS/XPath selector that'd run against a whole set of pages would require passing a lot of context to the model. The token limit is already the major limitation.
* The current solution does not require any changes when a page changes.  A selector-based model would require retraining every time a page changes as well as a means to detect such changes.
* For some data, selectors alone are not enough. The current model can easily extract all of the addresses from a page and break them into city/state/etc. A selector-based model would not be able to do this.

I do think there is room for hybrid approaches, and I plan to continue to explore them.

## Does the model "hallucinate" data?

It is possible, but in practice hasn't been observed as a major problem yet.

Because the *temperature* is zero, the output is fully deterministic and seems less likely to hallucinate data.

It is definitely possible however, and future versions of this tool will allow for automated error checking (and possibly correction).

## How much did you spend developing this?

So far, about $25 on API calls, switching to GPT-3.5 as the default made a big difference.

My most expensive call was a paginated GPT-4 call that cost $2.20.  I decided to add the cost-limiting features after that.

## What's with the license?

I'm still working on figuring this out.

For now, if you're working in a commercial setting and the license scares you away, that's fine.

If you really want to, you can contact me and we can work something out.