test:
	poetry run pytest

lint:
	poetry run ruff
	poetry run black --check

tutorial_output:
	poetry run python docs/tutorial_code/v2.py > docs/tutorial_code/v2.log
	poetry run python docs/tutorial_code/v3.py > docs/tutorial_code/v3.log
	poetry run python docs/tutorial_code/v5.py > docs/tutorial_code/v5.log
	poetry run sh docs/tutorial_code/cli.sh > docs/tutorial_code/cli.log

release type:  # patch, minor, major
	poetry version {{type}}
	poetry build
	poetry run mkdocs gh-deploy
	poetry publish
	git commit -m "release $(poetry version -s)"
	git tag $(poetry version -s)
	git push --tags
	# gh release create $(poetry version -s) -F docs/changelog.md