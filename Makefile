build:
	uv build

install:
	uv tool install dist/*.whl

run: build install
	database

check:
	uvx twine check dist/*

lint:
	uv run ruff check .

env:
	source .venv/bin/activate
