# QuestForge Backend API & Celery Worker Dockerfile
FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/pyproject.toml .
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy alembic psycopg2-binary redis celery jinja2 anthropic pyjwt bcrypt python-multipart requests httpx pytest pytest-cov pytest-asyncio

# Copy application code and prompt templates
COPY backend/ /app/backend/
COPY prompts/ /app/prompts/

# Create unprivileged application user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/bash appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Default entrypoint runs the FastAPI uvicorn server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
