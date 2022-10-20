#
# vim:ft=make
# Makefile
#
.DEFAULT_GOAL := help
.PHONY: test help

GLUE_CONTAINER := glue-starter-kit-glue

S3_BUCKET := s3://test-bucket
S3_TEST_DATA_PATH := $(S3_BUCKET)/testdata
S3_GLUE_ROOT := $(S3_BUCKET)/glue
S3_GLUE_SCRIPT_PATH := $(S3_GLUE_ROOT)/scripts

GLUE_JOB_NAME := glue_starter_kit
GLUE_JOB_JSON := job/$(GLUE_JOB_NAME).json

SRC_GLUE_MAIN := app.py
SRC_GLUE_LIBZIP := lib.zip

JOB_PARAM1 := 2022-10-12
GLUE_JOB_ARGS := '{"--JOB_NAME":"$(GLUE_JOB_NAME)","--PARAM1":"$(JOB_PARAM1)"}'

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
	poetry run flake8 --config=.config/flake8 src tests
	poetry run mypy --config=.config/mypy .

format: ## Formats you code with Black
	poetry run isort .
	poetry run black .

test: hidden ## run pytest
	sudo docker exec -it $(GLUE_CONTAINER) /home/glue_user/.local/bin/pytest -vs tests/

build: install lint test ## Create package for glue job
	mkdir -p dist
	rm -rf dist/*
	cp src/$(SRC_GLUE_MAIN) dist/
	cd src && zip -r ../dist/$(SRC_GLUE_LIBZIP) . -x '*__pycache__*' '*.pytest_cache*'

bumpversion: build ## bumpversion
	poetry run bump2version --tag --current-version $$(git describe --tags --abbrev=0) --tag-name '{new_version}' patch
	git push
	git push --tags

local-submit: build ## run `glue-spark-submit`
	sudo docker exec -it $(GLUE_CONTAINER) /home/glue_user/spark/bin/spark-submit dist/$(SRC_GLUE_MAIN) \
	    --py-files dist/$(SRC_GLUE_LIBZIP) \
	    --JOB_NAME='dummy' \
		--PARAM1=$(JOB_PARAM1)

fixture: ## Create test data
	python fixtures/make_fixture.py

send-awslocal: ## Send test data to local aws
	awslocal s3 cp --recursive fixtures/data/it/ $(S3_TEST_DATA_PATH)/

send-aws: ## Send test data to aws
	aws s3 cp --recursive fixtures/data/it/ $(S3_TEST_DATA_PATH)/

skeleton: ## Outputs a skeleton of the JSON definition of a glue job
	mkdir -p job
	aws glue create-job --generate-cli-skeleton > job/skeleton.json

deploy: build ## Deploy a glue job
	aws s3 cp --recursive dist/ $(S3_GLUE_SCRIPT_PATH)/
	aws glue delete-job --job-name $(GLUE_JOB_NAME)
	aws glue create-job --cli-input-json file://./$(GLUE_JOB_JSON)

start-job-run:
	aws glue start-job-run \
		--job-name $(GLUE_JOB_NAME) \
		--arguments $(GLUE_JOB_ARGS)
