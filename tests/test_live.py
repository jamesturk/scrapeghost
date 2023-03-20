"""
These tests require hitting the live API.

This means they require an API key, and cost money to run.
"""
import pytest
from scrapeghost import SchemaScraper

simple_html = """
<html><body>
<header>
<img src="site-logo.png" />
<ul>
<li><a href="/">Home</a></li>
<li><a href="/about">About</a></li>
<li><a href="/contact">Contact</a></li>
</ul>
</header>
<h1>Dave Bautista</h1>
<img src="https://example.com/dave.jpg" />
<ul>
<li><span class="movie">Guardians of the Galaxy</span> - Drax</li>
<li><span class="movie">Spectre</span> - Mr. Hinx </li>
<li><span class="movie">Blade Runner 2049</span> - Sapper Morton</li>
<li><span class="movie">Glass Onion</span> - Duke Cody</li>
<li>Dave also played Glossu Rabban Harkonnen in Dune.</li>
</ul>
</body></html>
"""


def test_simple_html():
    schema = {
        "actor": "string",
        "image": "url",
        "roles": {"name": "string", "character": "string"},
    }
    scraper = SchemaScraper(schema)
    result = scraper.scrape(simple_html)
    assert result == {
        "actor": "Dave Bautista",
        "image": "https://example.com/dave.jpg",
        "roles": [
            {"name": "Guardians of the Galaxy", "character": "Drax"},
            {"name": "Spectre", "character": "Mr. Hinx"},
            {"name": "Blade Runner 2049", "character": "Sapper Morton"},
            {"name": "Glass Onion", "character": "Duke Cody"},
            {"name": "Dune", "character": "Glossu Rabban Harkonnen"},
        ],
    }
    assert scraper.total_cost == pytest.approx(0.000868)
