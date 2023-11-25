from unittest.mock import patch
import openai


def _mock_response(**kwargs):
    mr = openai.types.completion.Completion(
        model=kwargs.get("model", ""),
        object="text_completion",
        choices=[
            openai.types.completion.CompletionChoice(
                index=0,
                text="",
                message=openai.types.chat.ChatCompletionMessage(content=kwargs.get("content", "hello world"), role="assistant"),
                finish_reason= kwargs.get("finish_reason", "stop"),
                logprobs={},
            )
        ],
        usage={
            "prompt_tokens": kwargs.get("prompt_tokens", 1),
            "completion_tokens": kwargs.get("completion_tokens", 1),
            "total_tokens": kwargs.get("prompt_tokens", 1) + kwargs.get("completion_tokens", 1),
        },
        created=1629200000,
        id="cmpl-xxxxxxxxxxxxxxxxxxxx",
        model_version=kwargs.get("model_version", "ada"),
        prompt="Hello world",
        status="complete",
        finish_reason="stop",
    )

    return mr


def _timeout(**kwargs):
    raise openai.APITimeoutError(request=None)


def patch_create():
    p = patch("scrapeghost.apicall.client.chat.completions.create")
    return p
