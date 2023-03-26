from unittest.mock import patch
import openai


def _mock_response(**kwargs):
    mr = openai.openai_object.OpenAIObject.construct_from(
        dict(
            model=kwargs.get("model"),
            choices=[
                {
                    "finish_reason": kwargs.get("finish_reason", "stop"),
                    "message": {
                        "content": kwargs.get("content", "Hello world"),
                    },
                }
            ],
            usage={
                "prompt_tokens": kwargs.get("prompt_tokens", 1),
                "completion_tokens": kwargs.get("completion_tokens", 1),
            },
            created=1629200000,
            id="cmpl-xxxxxxxxxxxxxxxxxxxx",
            model_version=kwargs.get("model_version", "ada"),
            prompt="Hello world",
            status="complete",
        )
    )

    return mr


def _timeout(**kwargs):
    raise openai.error.Timeout()


def patch_create():
    p = patch("scrapeghost.apicall.openai.ChatCompletion.create")
    return p
