.PHONY: help install dev run test lint format typecheck check clean

PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Create a venv and install the project with dev extras
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

dev: ## Run the Flask dev server with auto-reload
	$(BIN)/flask --app app run --debug

run: ## Run the Flask server without debug mode
	$(BIN)/flask --app app run

test: ## Run the test suite
	$(BIN)/pytest

lint: ## Lint with ruff
	$(BIN)/ruff check .

format: ## Format with ruff
	$(BIN)/ruff format .

typecheck: ## Type-check with mypy
	$(BIN)/mypy app

check: typecheck lint test ## Run typecheck → lint → tests (CI gate)

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build *.egg-info
	find . -path ./$(VENV) -prune -o -name __pycache__ -exec rm -rf {} +
