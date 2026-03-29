COMPOSE_RUN := docker compose run --rm mail-transfer

install:
	$(COMPOSE_RUN) uv sync

test:
	$(COMPOSE_RUN) uv run pytest

lint:
	$(COMPOSE_RUN) sh -c "uv run ruff check . && uv run mypy ."

format:
	$(COMPOSE_RUN) uv run ruff format .

run:
	$(COMPOSE_RUN) dotenvx run --env-file .env.encrypted -- uv run python -m src.main
