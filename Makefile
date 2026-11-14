.PHONY: help install dev dev-worker dev-frontend test test-cov seed lint docker-build up down clean

help:
	@echo "QuestForge Development & Deployment Commands:"
	@echo "  make install      - Install backend and frontend dependencies"
	@echo "  make dev          - Run backend FastAPI dev server on :8000"
	@echo "  make dev-worker   - Run Celery background worker"
	@echo "  make dev-frontend - Run Next.js frontend dev server on :3000"
	@echo "  make test         - Run pytest unit and integration suite"
	@echo "  make test-cov     - Run pytest with minimum 80% coverage check"
	@echo "  make seed         - Seed database with rubrics, users & sample questions"
	@echo "  make lint         - Run ruff linting checks on backend"
	@echo "  make up           - Spin up full docker-compose stack"
	@echo "  make down         - Stop docker-compose stack"
	@echo "  make clean        - Remove caches, test DBs, and build artifacts"

install:
	pip install -e ./backend
	cd frontend && npm install

dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker:
	celery -A backend.app.workers.celery_app worker --loglevel=info --concurrency=4

dev-frontend:
	cd frontend && npm run dev

test:
	python -m pytest backend/tests/ -v

test-cov:
	python -m pytest backend/tests/ -v \
		--cov=backend/app/pipeline \
		--cov-report=term-missing \
		--cov-fail-under=80

seed:
	python -c "from backend.app.database import SessionLocal; from backend.app.seed.seed_data import seed_initial_data; db = SessionLocal(); seed_initial_data(db); db.close()"

lint:
	ruff check backend/app

docker-build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f test_questforge.db test_ci.db
	rm -rf .pytest_cache .coverage
