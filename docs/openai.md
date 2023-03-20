# About the OpenAI API

This section assumes you are mostly unfamiliar with the OpenAI API and aims to provide a high-level overview of how they work in relation to this library. 


## API Keys

To use the OpenAI API you will need an API key.  You can get one by [creating an account](https://platform.openai.com/signup) and then [creating an API key](https://platform.openai.com/account/api-keys).

Once an API key is created, you can set it as an environment variable:

```bash
export OPENAI_API_KEY=sk-...
```

You can also set the API Key directly in Python:

```python
import openai

openai.api_key_path = "~/.openai-key"
#  - or -
openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```


## Costs

The OpenAI API is considerably expensive.
The cost of a call varies based on the model used and the size of the input.

The cost estimates provided by this library are based on the [OpenAI pricing page](https://platform.openai.com/pricing) and not guaranteed to be accurate.

Fortunately, <https://platform.openai.com/account/billing/limits> lets you set a soft & hard limit so that you can't accidentally run up a large bill.

It is **highly recommended** that you set a low usage limit on your API key to avoid accidentally running up a large bill.

--8<--
_cost.md
--8<--

## Tokens

OpenAI encodes text using a tokenizer, which converts words to integers.

You'll see that billing is based on the number of tokens used.  A token is approximately 3 characters, so 3000 characters of HTML will roughly correspond to 1000 tokens.

Additionally, the GPT-3-Turbo model is limited to 4096 tokens.  GPT-4 is limited to 8192 tokens.  (A 32k model has been announced, but is not yet widely available.)

Various features in the library will help you avoid running into token limits, but it is still very common to exceed them in practice.

If your pages exceed them, you'll need to focus on improving your [selectors](#selectors) so that only the required data is sent to the underlying models.

## Prompts

The OpenAI API provides a chat-like interface, where there are three roles: *system*, *user*, and *assistant*.  The *system* commands provide guidance to the *assistant* on how it should perform its tasks.  The *user* provides a query to the *assistant*, which is then answered.

In practice, this results in a prompt that looks like something this:

**System:** For the given HTML, convert to a list of JSON objects matching this schema: `{"name": "string", "age": "number"}`

**System:** Be sure to provide valid JSON that is not truncated and contains no extra fields beyond those in the schema.

**User:** `<html><div><h2>Joe</h2><span>Age: 42</span></div></html>`

**Assistant**: `{"name": "Joe", "age": 42}`

It is possible to adjust the system commands the library sends, but the goal is to provide a simple default prompt that works well for most use cases.

TODO: link to docs