import pytest
import lxml.html
from scrapeghost.responses import ScrapeResponse
from scrapeghost.postprocessors import HallucinationChecker, PostprocessingError


def test_hallucination_checker():
    response = ScrapeResponse(
        parsed_html=lxml.html.fromstring(
            """<a href="https://example.com">Moltar</a><p>Director</p>"""
        ),
        data={"name": "Moltar", "role": "Director", "url": "https://example.com"},
    )

    # no hallucination
    hpp = HallucinationChecker()
    hpp(response, None)

    # hallucination
    response.data["last_name"] = "Moltanski"
    with pytest.raises(PostprocessingError):
        hpp(response, None)


def test_hallucination_checker_list():
    response = ScrapeResponse(
        parsed_html=lxml.html.fromstring(
            "<div><li><a href='https://example.com/moltar'>Moltar</a></li>"
            "<li><a href='https://example.com/brak'>Brak</a></li></div>"
        ),
        data=[
            {"name": "Moltar", "url": "https://example.com/moltar"},
            {"name": "Brak", "url": "https://example.com/brak"},
        ],
    )

    # no hallucination
    hpp = HallucinationChecker()
    hpp(response, None)

    response.data[0]["last_name"] = "Moltanski"

    # hallucination
    with pytest.raises(PostprocessingError):
        hpp(response, None)
