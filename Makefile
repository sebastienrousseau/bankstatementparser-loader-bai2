.PHONY: help install dev test lint format type-check security clean examples doc-coverage check

PYTHON ?= python3
POETRY ?= poetry

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(POETRY) install --only main

dev: ## Install all dependencies (including dev)
	$(POETRY) install

test: ## Run tests with the 100% line+branch coverage gate
	$(POETRY) run pytest tests/ \
		--cov=bankstatementparser_loader_bai2 --cov-branch \
		--cov-report=term-missing --cov-fail-under=100 -v

lint: ## Run linters (ruff + black check)
	$(POETRY) run ruff check bankstatementparser_loader_bai2/ tests/
	$(POETRY) run black --check bankstatementparser_loader_bai2/ tests/

format: ## Auto-format code (ruff fix + black)
	$(POETRY) run ruff check --fix bankstatementparser_loader_bai2/ tests/
	$(POETRY) run black bankstatementparser_loader_bai2/ tests/

type-check: ## Run mypy type checking
	$(POETRY) run mypy bankstatementparser_loader_bai2/

security: ## Run security scan (bandit)
	$(POETRY) run bandit -r bankstatementparser_loader_bai2/ -c pyproject.toml 2>/dev/null || \
		$(POETRY) run bandit -r bankstatementparser_loader_bai2/ -ll

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	rm -rf coverage.xml .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true

examples: ## Verify example scripts run
	$(POETRY) run python examples/01_load_transactions.py
	$(POETRY) run python examples/02_summarize_file.py

doc-coverage: ## Enforce the 100% docstring coverage gate
	$(POETRY) run interrogate -c pyproject.toml -v bankstatementparser_loader_bai2

check: lint type-check test doc-coverage examples ## Run all gates
