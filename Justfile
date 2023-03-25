test:
	poetry run pytest --cov=src/ --cov-report html

lint:
	poetry run ruff
	poetry run black --check

docs:
	poetry run mkdocs serve

examples:
	poetry run sh docs/examples/cli.sh > docs/examples/cli.log
	poetry run python docs/examples/pydantic_example.py > docs/examples/pydantic_example.log
	# poetry run python docs/examples/episode_scraper_1.py > docs/examples/episode_scraper_1.log
	poetry run python docs/examples/tutorial/episode_scraper_2.py > docs/examples/tutorial/episode_scraper_2.log
	poetry run python docs/examples/tutorial/episode_scraper_3.py > docs/examples/tutorial/episode_scraper_3.log
	poetry run python docs/examples/tutorial/episode_scraper_4.py > docs/examples/tutorial/episode_scraper_4.log
	poetry run python docs/examples/tutorial/episode_scraper_5.py > docs/examples/tutorial/episode_scraper_5.log
	# poetry run python docs/examples/tutorial/list_scraper_1.py > docs/examples/tutorial/list_scraper_1.log
	poetry run python docs/examples/tutorial/list_scraper_v2.py > docs/examples/tutorial/list_scraper_v2.log


release type:  # patch, minor, major
	poetry version {{type}}
	poetry build
	poetry run mkdocs gh-deploy
	poetry publish
	git commit -am "release $(poetry version -s)"
	git tag $(poetry version -s)
	git push --tags
	gh release create $(poetry version -s) -F docs/changelog.md