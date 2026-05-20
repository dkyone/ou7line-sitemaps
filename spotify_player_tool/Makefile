.PHONY: help install dev test lint format clean run batch

help:
	@echo "Spotify Player Image Tool - Available Commands"
	@echo "─────────────────────────────────────────────"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install dependencies"
	@echo "  make install-dev     Install dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev             Run development server (auto-reload)"
	@echo "  make run             Run production server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test            Run tests"
	@echo "  make test-cov        Run tests with coverage"
	@echo "  make lint            Run linters (flake8)"
	@echo "  make format          Format code with black"
	@echo "  make format-check    Check code formatting"
	@echo ""
	@echo "Batch Processing:"
	@echo "  make batch URL=<url> STYLE=all   Process playlist"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           Remove cache and build files"
	@echo ""

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run:
	./run.sh

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

lint:
	flake8 . --exclude=.venv,venv,__pycache__,.pytest_cache

format:
	black . --line-length=100

format-check:
	black . --check --line-length=100

batch:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make batch URL=<spotify_url> [STYLE=all|dark|light|blur|gradient]"; \
		exit 1; \
	fi
	./batch.sh "$(URL)" "$(STYLE)"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -name .coverage -delete 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/ 2>/dev/null || true

.DEFAULT_GOAL := help
