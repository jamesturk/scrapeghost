from scrapeghost import SchemaScraper
from scrapeghost.postprocessors import JSONPostprocessor


def test_bad_json_nudge():
    # single quotes, trailing commas
    bad_json = "{'name': 'phil', }"
    jpp = JSONPostprocessor(nudge=True)
    repaired = jpp(scraper=SchemaScraper({"name": "string"}), data=bad_json)
    assert repaired == {"name": "phil"}
