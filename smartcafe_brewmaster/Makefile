.PHONY: help setup clean test run init ingest report

help:
	@echo "SmartCafé BrewMaster - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup          Install dependencies"
	@echo "  make test           Run full test suite"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make clean          Remove generated files"
	@echo "  make init          Initialize database"
	@echo "  make ingest        Process IoT CSV files"
	@echo "  make report        Generate daily reports"
	@echo "  make lint          Run linters (if configured)"

setup:
	pip install -r requirements.txt

test:
	pytest -v

test-cov:
	pytest --cov=smartcafe_brewmaster --cov-report=html tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

init:
	python -m smartcafe_brewmaster.api.cli init-db

ingest:
	python -m smartcafe_brewmaster.api.cli ingest

report:
	python -m smartcafe_brewmaster.api.cli report

.DEFAULT_GOAL := help
