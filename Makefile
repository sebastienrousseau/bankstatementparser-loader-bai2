.PHONY: help install dev test lint format fuzz docs demo type-check security clean examples doc-coverage mutation complexity check

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
	$(POETRY) run ruff check bankstatementparser_loader_bai2/ tests/ benches/ fuzz/
	$(POETRY) run black --check bankstatementparser_loader_bai2/ tests/ benches/ fuzz/

format: ## Auto-format code (ruff fix + black)
	$(POETRY) run ruff check --fix bankstatementparser_loader_bai2/ tests/ benches/ fuzz/
	$(POETRY) run black bankstatementparser_loader_bai2/ tests/ benches/ fuzz/

fuzz: ## Fuzz the BAI2 loader with Atheris for 60s (Linux x86_64, Python 3.12+)
	$(POETRY) install --with fuzz
	mkdir -p .fuzz-corpus
	$(POETRY) run python fuzz/fuzz_load_bai2.py .fuzz-corpus fuzz/corpus tests/fixtures/real -max_total_time=60

type-check: ## Run mypy type checking
	$(POETRY) run mypy bankstatementparser_loader_bai2/

security: ## Run security scan (bandit)
	$(POETRY) run bandit -r bankstatementparser_loader_bai2/ -c pyproject.toml

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

mutation: ## Run mutation testing (mutmut) and print the kill score
	$(POETRY) run mutmut run
	$(POETRY) run mutmut results

demo: ## Render the README demo GIF with VHS
	vhs .github/demo.tape

docs: ## Build the user manual (mkdocs --strict) into site/
	$(POETRY) install --with docs
	NO_MKDOCS_2_WARNING=1 $(POETRY) run mkdocs build --strict

# Per-function ceilings (cyclomatic 10, cognitive 15, Halstead 30,
# 60 lines; 500 lines per file) against scripts/complexity_baseline.json,
# which may only shrink. Record an improvement with
# `python3 scripts/check_complexity.py --update`.
complexity: ## Enforce the complexity baseline
	$(PYTHON) scripts/check_complexity.py

check: lint type-check complexity test doc-coverage examples ## Run all gates
