#!/bin/sh
set -e
uv sync --quiet
exec "$@"
