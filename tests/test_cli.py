import typer
from typer.testing import CliRunner
from scrapeghost.cli import scrape

runner = CliRunner()
app = typer.Typer()
app.command()(scrape)


def test_cli_no_schema():
    result = runner.invoke(
        app,
        [
            "https://scrapple.fly.dev/staff/2",
        ],
    )
    assert result.exit_code == 2
    assert "must provide" in result.stdout


def test_cli_schema_file():
    result = runner.invoke(
        app,
        [
            "--schema-file",
            "tests/name_schema.json",
            "https://scrapple.fly.dev/staff/2",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0
    assert "Jane" in result.stdout
    assert "Daikon" in result.stdout


def test_cli_basics():
    result = runner.invoke(
        app,
        [
            "--schema",
            '{"first_name": "str", "last_name": "str"}',
            "https://scrapple.fly.dev/staff/2",
        ],
    )
    assert result.exit_code == 0
    assert "Jane" in result.stdout
    assert "Daikon" in result.stdout
