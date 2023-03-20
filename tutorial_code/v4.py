from scrapeghost import SchemaScraper, CSS

episode_list_scraper = SchemaScraper({"episode_urls": ["str"]})
episode_list_scraper("https://comedybangbang.fandom.com/wiki/Category:Episodes")
