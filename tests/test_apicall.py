import pytest
from unittest.mock import patch
from scrapeghost.apicall import OpenAiCall, RetryRule
from scrapeghost.errors import MaxCostExceeded
import openai


def _mock_response(**kwargs):
    mr = openai.openai_object.OpenAIObject.construct_from(
        dict(
            object="text_completion",
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


def test_basic_call():
    api_call = OpenAiCall(
        models=["gpt-3.5-turbo"],
    )
    # mock openai.ChatCompletion.create
    with patch_create() as create:
        create.side_effect = _mock_response
        api_call.request("<html>")
    assert create.call_count == 1
    assert create.call_args.kwargs["model"] == "gpt-3.5-turbo"
    assert api_call.total_cost == 0.000004


def test_model_fallback():
    api_call = OpenAiCall(
        models=["gpt-3.5-turbo", "gpt-4"],
        retry=RetryRule(1, 0),  # disable wait
    )
    with patch_create() as create:
        # fail first request
        create.side_effect = [
            _mock_response(finish_reason="timeout"),
            _mock_response(),
        ]
        api_call.request("<html>")
    assert create.call_count == 2
    assert create.call_args.kwargs["model"] == "gpt-4"


def test_normal_retry():
    api_call = OpenAiCall(
        models=["gpt-3.5-turbo"],
        retry=RetryRule(1, 0),  # disable wait
    )

    def _timeout_once(**kwargs):
        if _timeout_once.called:
            return _mock_response()
        _timeout_once.called = True
        raise openai.error.Timeout()

    _timeout_once.called = False

    with patch_create() as create:
        # fail first request
        create.side_effect = _timeout_once
        api_call.request("<html>")
    assert create.call_count == 2
    assert create.call_args.kwargs["model"] == "gpt-3.5-turbo"


def test_retry_failure():
    api_call = OpenAiCall(
        models=["gpt-3.5-turbo"],
        retry=RetryRule(2, 0),  # disable wait
    )

    with pytest.raises(openai.error.Timeout):
        with patch_create() as create:
            # fail first request
            create.side_effect = _timeout
            api_call.request("<html>")

    assert create.call_count == 3


def test_max_cost_exceeded():
    api_call = OpenAiCall()
    with patch_create() as create:
        create.side_effect = lambda **kwargs: _mock_response(
            prompt_tokens=1000, completion_tokens=1000
        )
        with pytest.raises(MaxCostExceeded):
            for _ in range(300):
                api_call.request("<html>" * 1000)


def test_stats():
    api_call = OpenAiCall()
    with patch_create() as create:
        create.side_effect = lambda **kwargs: _mock_response(
            prompt_tokens=1000, completion_tokens=100
        )
        for _ in range(20):
            api_call.request("<html>")

    assert api_call.stats() == {
        "total_cost": pytest.approx(0.044),
        "total_prompt_tokens": 20000,
        "total_completion_tokens": 2000,
    }
