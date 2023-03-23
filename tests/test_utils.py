import pytest
from scrapeghost import utils


@pytest.mark.parametrize(
    "model,pt,ct,total",
    [
        ("gpt-4", 1000, 1000, 0.09),
        ("gpt-3.5-turbo", 1000, 1000, 0.004),
        ("gpt-3.5-turbo", 2000, 2000, 0.008),  # near max
        ("gpt-4", 4000, 4000, 0.36),  # near max
    ],
)
def test_cost_calc(model, pt, ct, total):
    assert utils._cost(model, pt, ct) == total


def test_cost_estimate():
    assert utils.cost_estimate("hello" * 1000, "gpt-3.5-turbo") == pytest.approx(0.003)
    assert utils.cost_estimate("hello" * 1000, "gpt-4") == pytest.approx(0.06)
