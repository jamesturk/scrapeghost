# Command Line Interface

scrapeghost offers a command line interface which is particularly useful for experimentation.

It is also possible to use as a step in a data pipeline.

## Configuration

In order to use the CLI, the `OPENAI_API_KEY` environment variable must be set.

## Usage

```{bash}
scrapeghost --help
 Usage: scrapeghost [OPTIONS] URL                                                                                                                                            
╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────╮
│ *    url      TEXT  [default: None] [required]                                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --xpath                         TEXT     XPath selector to narrow the scrape [default: None]        │
│ --css                           TEXT     CSS selector to narrow the scrape [default: None]          │
│ --schema                        TEXT     Schema to use for scraping [default: None]                 │
│ --schema-file                   PATH     Path to schema.json file [default: None]                   │
│ --gpt4             --no-gpt4             Use GPT-4 instead of GPT-3.5-turbo [default: no-gpt4]      │
│ --verbose      -v               INTEGER  Verbosity level 0-2 [default: 0]                           │
│ --help                                   Show this message and exit.                                │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
