import pathlib
import logging
import structlog
import typer
from .scrapers import SchemaScraper


def scrape(
    url: str,
    xpath: str | None = None,
    css: str | None = None,
    schema: str | None = None,
    schema_file: pathlib.Path | None = None,
    gpt4: bool = False,
    verbosity: int = typer.Option(0, "-v", "--verbose", count=True),
):
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
    result = scraper(url, xpath=xpath, css=css)
    typer.echo(result)


def main():
    typer.run(scrape)


if __name__ == "__main__":
    main()
