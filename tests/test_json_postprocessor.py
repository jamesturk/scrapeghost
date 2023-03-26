import pytest
from scrapeghost import SchemaScraper
from scrapeghost.postprocessors import JSONPostprocessor
from scrapeghost.responses import Response
from scrapeghost.errors import InvalidJSON, PostprocessingError
from testutils import patch_create, _mock_response


def test_json_already_processed():
    # already processed
    jpp = JSONPostprocessor()
    r = Response(data={})
    with pytest.raises(PostprocessingError):
        jpp(r, scraper=SchemaScraper({"name": "string"}))


def test_json_no_nudge():
    # single quotes, trailing commas
    bad_json = "{'name': 'phil', }"
    jpp = JSONPostprocessor(nudge=False)
    r = Response(data=bad_json)
    with pytest.raises(InvalidJSON):
        jpp(r, scraper=SchemaScraper({"name": "string"}))
    assert "False" in str(jpp)


def test_json_nudge():
    # single quotes, trailing commas
    bad_json = "{'name': 'phil', }"
    jpp = JSONPostprocessor(nudge=True)
    r = Response(data=bad_json)
    with patch_create() as create:
        create.side_effect = lambda **kwargs: _mock_response(content='{"name": "phil"}')
        repaired = jpp(r, scraper=SchemaScraper({"name": "string"}))
    assert len(repaired.api_responses) == 1
    assert repaired.data == {"name": "phil"}


def test_nudge_fails():
    # single quotes, trailing commas
    bad_json = "{'name': 'phil', }"
    jpp = JSONPostprocessor(nudge=True)
    r = Response(data=bad_json)
    with pytest.raises(InvalidJSON):
        with patch_create() as create:
            create.side_effect = lambda **kwargs: _mock_response(
                content='{"name": "phil'
            )
            jpp(r, scraper=SchemaScraper({"name": "string"}))
