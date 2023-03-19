import pathlib
import typer
from .scrapers import SchemaScraper


def scrape(
    url: str,
    xpath: str | None = None,
    css: str | None = None,
    schema: str | None = None,
    schema_file: pathlib.Path | None = None,
):
    if schema_file:
        with open(schema_file) as f:
            schema = f.read()
    if not schema:
        raise typer.BadParameter("You must provide a schema or schema_file.")
    scraper = SchemaScraper(schema)
    result = scraper(url, xpath=xpath, css=css)
    typer.echo(result)


if __name__ == "__main__":
    typer.run(scrape)
