import os
import pytest
from scrapeghost import SchemaScraper
from scrapeghost.postprocessors import JSONPostprocessor

api_key_is_set = os.getenv("OPENAI_API_KEY", "")


@pytest.mark.skipif(not api_key_is_set, reason="requires API key")
def test_bad_json_nudge():
    # single quotes, trailing commas
    bad_json = "{'name': 'phil', }"
    jpp = JSONPostprocessor(nudge=True)
    repaired = jpp(scraper=SchemaScraper({"name": "string"}), data=bad_json)
    assert repaired == {"name": "phil"}
