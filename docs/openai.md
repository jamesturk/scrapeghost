# OpenAI / GPT

This section assumes you are mostly unfamiliar with the OpenAI API and aims to provide a high-level overview of how it works in relation to this library. 


## API Keys

--8<-- "docs/snippets/_apikey.md"

## Costs

The OpenAI API is considerably expensive.

The cost of a call varies based on the model used and the size of the input.

The cost estimates provided by this library are based on the [OpenAI pricing page](https://platform.openai.com/pricing) and not guaranteed to be accurate.

--8<-- "docs/snippets/_cost.md"

## Tokens

OpenAI encodes text using a [tokenizer](https://github.com/openai/tiktoken), which converts words to integers.

You'll see that billing is based on the number of tokens used.  A token is approximately 3 characters, so 3000 characters of HTML will roughly correspond to 1000 tokens.

!!! warning

    In practice, the above estimate turns out to be a bit low.  Part of the issue is that HTML does not tokenize particularly efficiently.  "Hello world!" is three tokens, but "<b>Hello world!</b>" is nine!

    You can experiment via https://platform.openai.com/tokenizer


Models are limited to a maximum number of tokens.  For example, the default GPT-3.5-turbo model is limited to 4096 tokens.  GPT-4's default limit is 8192.  Both models have larger versions available, but they are more expensive.

Various features in the library will help you avoid running into token limits, but it is still very common to exceed them in practice.

If your pages exceed these limits, you'll need to focus on improving your [selectors](/api.md#selectors) so that only the required data is sent to the underlying models.

## Prompts

The OpenAI API provides a chat-like interface, where there are three roles: *system*, *user*, and *assistant*.  The *system* commands provide guidance to the *assistant* on how it should perform its tasks.  The *user* provides a query to the *assistant*, which is then answered.

In practice, this results in a prompt that looks like something this:

**System:** For the given HTML, convert to a list of JSON objects matching this schema: `{"name": "string", "age": "number"}`

**System:** Be sure to provide valid JSON that is not truncated and contains no extra fields beyond those in the schema.

**User:** `<html><div><h2>Joe</h2><span>Age: 42</span></div></html>`

**Assistant**: `{"name": "Joe", "age": 42}`

It is possible to adjust the system commands the library sends, but the goal is to provide a simple default prompt that works well for most use cases.