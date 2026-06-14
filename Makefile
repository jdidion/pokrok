module = pokrok

.PHONY: all install test lint format build clean

all: build

install:
	uv sync

test:
	uv run pytest --cov --cov-report term-missing

lint:
	uv run ruff check $(module) tests

format:
	uv run ruff format $(module) tests

build:
	uv build

clean:
	rm -rf build dist *.egg-info
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
