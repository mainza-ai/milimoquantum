#!/bin/bash
# Milimo Quantum — Start Native Celery Worker (Apple Silicon)
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/backend"

echo "⚛ Activating python environment..."
source milimoenv/bin/activate

echo "⚛ Starting Celery worker with MLX hardware acceleration..."
export LLM_BACKEND=mlx

# Docker infrastructure connection (use localhost from host machine)
export DATABASE_URL="postgresql://milimo:milimopassword@localhost:5432/milimoquantum"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/1"
export NEO4J_URI="bolt://localhost:7687"
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"

celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
