import os
import pytest
from scrapeghost import SchemaScraper
from scrapeghost.postprocessors import JSONPostprocessor
from scrapeghost.responses import Response

api_key_is_set = os.getenv("OPENAI_API_KEY", "")


@pytest.mark.skipif(not api_key_is_set, reason="requires API key")
def test_bad_json_nudge():
    # single quotes, trailing commas
    bad_json = "{'name': 'phil', }"
    jpp = JSONPostprocessor(nudge=True)
    r = Response(data=bad_json)
    repaired = jpp(r, scraper=SchemaScraper({"name": "string"}))
    assert len(repaired.api_responses) == 1
    assert repaired.data == {"name": "phil"}
