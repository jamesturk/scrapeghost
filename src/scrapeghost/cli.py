import json
import pathlib
import logging
import structlog
import typer
from .scrapers import SchemaScraper
from .preprocessors import CSS, XPath


def scrape(
    url: str,
    xpath: str = typer.Option(None, help="XPath selector to narrow the scrape"),
    css: str = typer.Option(None, help="CSS selector to narrow the scrape"),
    schema: str = typer.Option(None, help="Schema to use for scraping"),
    schema_file: pathlib.Path = typer.Option(None, help="Path to schema.json file"),
    gpt4: bool = typer.Option(False, help="Use GPT-4 instead of GPT-3.5-turbo"),
    verbosity: int = typer.Option(
        0, "-v", "--verbose", count=True, help="Verbosity level 0-2"
    ),
) -> None:
    if schema_file:
        with open(schema_file) as f:
            schema = f.read()
    if not schema:
        raise typer.BadParameter("You must provide a schema or schema_file.")

    log_level = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}[verbosity]
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )

    scraper = SchemaScraper(schema, models=["gpt-4"] if gpt4 else ["gpt-3.5-turbo"])
    if xpath:
        scraper.preprocessors.append(XPath(xpath))
    if css:
        scraper.preprocessors.append(CSS(css))
    result = scraper(url)
    typer.echo(json.dumps(result.data))


def main() -> None:
    typer.run(scrape)


if __name__ == "__main__":
    main()
