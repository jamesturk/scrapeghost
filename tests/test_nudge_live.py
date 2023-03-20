from scrapeghost import SchemaScraper, InvalidJSON


def test_bad_json_nudge():
    # single quotes, trailing commas
    e = InvalidJSON("Invalid JSON", "{'name': 'phil', }")
    schema = {"name": "string"}
    scraper = SchemaScraper(schema)
    result = scraper.nudge(e)
    assert result.message.content == '{"name": "phil"}'
