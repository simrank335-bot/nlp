# GraphRAG — Makefile
#
# Everything runs from the repository root. Python lives in backend/.venv,
# Node dependencies in frontend/node_modules.

ifeq ($(OS),Windows_NT)
PYTHON := .venv/Scripts/python.exe
UV_PYTHON := .venv/Scripts/python.exe
else
PYTHON := .venv/bin/python
UV_PYTHON := .venv/bin/python
endif

.PHONY: help install install-ml dev-api dev-web test test-cov build up down logs seed clean

help:
	@echo "install      create the Python venv and install backend + frontend deps"
	@echo "dev-api      run the API on :8000 with reload"
	@echo "dev-web      run the Vite dev server on :5173"
	@echo "test         run the backend test suite"
	@echo "build        type-check and build the frontend"
	@echo "up / down    start or stop the Docker Compose stack"
	@echo "seed         ingest data/samples and ask demo questions (API must be up)"

install:
	cd backend && uv venv --python 3.12 .venv
	cd backend && uv pip install --python $(UV_PYTHON) -r requirements.txt -r requirements-dev.txt
	cd frontend && npm install --no-audit --no-fund

install-ml:
	cd backend && uv pip install --python $(UV_PYTHON) -r requirements-ml.txt

dev-api:
	cd backend && PYTHONPATH=. $(PYTHON) -m uvicorn app.main:app --reload --port 8000

dev-web:
	cd frontend && npm run dev

test:
	cd backend && PYTHONPATH=. $(PYTHON) -m pytest -q

test-cov:
	cd backend && PYTHONPATH=. $(PYTHON) -m pytest --cov=app --cov-report=term-missing

build:
	cd frontend && npm run build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

seed:
	cd backend && $(PYTHON) scripts/seed_demo.py

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/data frontend/dist
