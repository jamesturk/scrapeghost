import json
from scrapeghost import SchemaScraper, CSS

episode_list_scraper = SchemaScraper(
    '{"url": "url"}',
    auto_split_length=2048,
    # restrict this to GPT-3.5-Turbo to keep the cost down
    models=["gpt-3.5-turbo"],
    extra_preprocessors=CSS(".mw-parser-output a[class!='image link-internal']"),
)

episode_scraper = SchemaScraper(
    {
        "title": "str",
        "episode_number": "int",
        "release_date": "YYYY-MM-DD",
        "guests": ["str"],
        "characters": ["str"],
    },
    extra_preprocessors=CSS("div.page-content"),
)

episode_urls = episode_list_scraper(
    "https://comedybangbang.fandom.com/wiki/Category:Episodes",
)
print(
    f"Scraped {len(episode_urls)} episode URLs, cost {episode_list_scraper.total_cost}"
)

episode_data = []
for episode_url in episode_urls:
    print(episode_url)
    episode_data.append(
        episode_scraper(
            episode_url["url"],
        )
    )

print(f"Scraped {len(episode_data)} episodes, cost {episode_scraper.total_cost}")

with open("episode_data.json", "w") as f:
    json.dump(episode_data, f, indent=2)
