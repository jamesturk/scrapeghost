test:
	poetry run pytest --cov=src/ --cov-report html

lint:
	poetry run ruff
	poetry run black --check

docs:
	poetry run mkdocs serve

examples:
	poetry run python docs/examples/tutorial/v2.py > docs/examples/tutorial/v2.log
	poetry run python docs/examples/tutorial/v3.py > docs/examples/tutorial/v3.log
	poetry run python docs/examples/tutorial/v5.py > docs/examples/tutorial/v5.log
	poetry run sh docs/examples/tutorial/cli.sh > docs/examples/tutorial/cli.log

release type:  # patch, minor, major
	poetry version {{type}}
	poetry build
	poetry run mkdocs gh-deploy
	poetry publish
	git commit -m "release $(poetry version -s)"
	git tag $(poetry version -s)
	git push --tags
	# gh release create $(poetry version -s) -F docs/changelog.md