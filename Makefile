build:
	uv sync
	uv build

install:
	uv tool install dist/*.whl

run: build install
	valutatrade-hub

check:
	uvx twine check dist/*

lint:
	uv run ruff check .

env:
	source .venv/bin/activate
