### Getting an API Key

To use the OpenAI API you will need an API key.  You can get one by [creating an account](https://platform.openai.com/signup) and then [creating an API key](https://platform.openai.com/account/api-keys).

It's **strongly recommended** that you set a usage limit on your API key to avoid accidentally running up a large bill.

<https://platform.openai.com/account/billing/limits> lets you set usage limits to avoid unpleasant surprises.

### Using your key

Once an API key is created, you can set it as an environment variable:

```bash
$ export OPENAI_API_KEY=sk-...
```

You can also set the API Key directly in Python:

```python
import openai

openai.api_key_path = "~/.openai-key"
#  - or -
openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Be careful not to expose this key to the public by checking it into a public repository.