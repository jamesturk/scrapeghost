import pytest
from scrapeghost.apicall import OpenAiCall, RetryRule
from scrapeghost.errors import MaxCostExceeded, TooManyTokens
import openai
from testutils import _mock_response, _timeout, patch_create


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
    assert api_call.total_cost == 0.000003


def test_model_fallback():
    api_call = OpenAiCall(
        models=["gpt-3.5-turbo", "gpt-4"],
        retry=RetryRule(1, 0),  # disable wait
    )
    with patch_create() as create:
        # fail first request
        create.side_effect = [
            _mock_response(finish_reason="length"),
            _mock_response(),
        ]
        api_call.request("<html>")
    assert create.call_count == 2
    assert create.call_args.kwargs["model"] == "gpt-4"


# " hi" is 1 token, " hi hi" is 2 tokens, etc.
def _make_n_tokens(n):
    return " hi" * n


def test_model_fallback_token_limit():
    api_call = OpenAiCall(
        models=["gpt-4", "gpt-3.5-turbo"],
        retry=RetryRule(1, 0),  # disable wait
    )
    with patch_create() as create:
        create.side_effect = [
            _mock_response(),
        ]
        api_call.request(_make_n_tokens(10000))

    # make sure we used the 16k model and only made one request
    assert create.call_count == 1
    assert create.call_args.kwargs["model"] == "gpt-3.5-turbo"


def test_model_fallback_token_limit_still_too_big():
    api_call = OpenAiCall(
        models=["gpt-4", "gpt-3.5-turbo"],
        retry=RetryRule(1, 0),  # disable wait
    )

    with pytest.raises(TooManyTokens):
        api_call.request(_make_n_tokens(20000))


def test_normal_retry():
    api_call = OpenAiCall(
        models=["gpt-3.5-turbo"],
        retry=RetryRule(1, 0),  # disable wait
    )

    def _timeout_once(**kwargs):
        if _timeout_once.called:
            return _mock_response()
        _timeout_once.called = True
        raise openai.APITimeoutError(request=None)

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

    with pytest.raises(openai.APITimeoutError):
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
            for _ in range(350):
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
        "total_cost": pytest.approx(0.042),
        "total_prompt_tokens": 20000,
        "total_completion_tokens": 2000,
    }
