#
# vim:ft=make
# Makefile
#
.DEFAULT_GOAL := help
.PHONY: test help


help:  ## these help instructions
	@sed -rn 's/^([a-zA-Z_-]+):.*?## (.*)$$/"\1" "\2"/p' < $(MAKEFILE_LIST)|xargs printf "make %-20s# %s\n"

hidden: # example undocumented, for internal usage only
	@true

pydoc: ## Run a pydoc server and open the browser
	poetry run python -m pydoc -b

install: ## Run `poetry install`
	poetry install

showdeps: ## run poetry to show deps
	@echo "CURRENT:"
	poetry show --tree
	@echo
	@echo "LATEST:"
	poetry show --latest

lint: ## Runs black, isort, bandit, flake8 in check mode
	poetry run black --check .
	poetry run isort --check .
	poetry run bandit -r src
	poetry run flake8 --config=setup.cfg src tests
	poetry run mypy --config=setup.cfg .

format: ## Formats you code with Black
	poetry run isort .
	poetry run black .

test: hidden ## run pytest with coverage
	poetry run pytest -v --cov glue_starter_kit

build: install lint test ## run `poetry build` to build source distribution and wheel
	poetry build

bumpversion: build ## bumpversion
	poetry run bump2version --tag --current-version $$(git describe --tags --abbrev=0) --tag-name '{new_version}' patch
	git push
	git push --tags
jupyter: ## run the jupyter-lab server
	poetry run jupyter-lab

run: ## run `poetry run glue-starter-kit`
	poetry run glue-starter-kit
