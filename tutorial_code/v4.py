from scrapeghost import SchemaScraper

episode_list_scraper = SchemaScraper({"episode_urls": ["str"]})
episode_list_scraper("https://comedybangbang.fandom.com/wiki/Category:Episodes")
