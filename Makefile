.PHONY: lint
lint:
	uv run ruff check .
	uv run mypy .

.PHONY: format
format:
	uv run ruff format .

.PHONY: run
run:
	dotenvx run -- python main.py uv run python main.py