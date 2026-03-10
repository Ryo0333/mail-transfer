.PHONY: test
test:
	uv run pytest

.PHONY: lint
lint:
	uv run ruff check .
	uv run mypy .

.PHONY: format
format:
	uv run ruff format .

.PHONY: run
run:
	dotenvx run -- python -m src.main