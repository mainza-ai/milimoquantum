#!/bin/bash
# Milimo Quantum — Rebuild & Start Docker Cluster
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Ensure Docker Desktop bin is in PATH for official binaries and plugins on macOS
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"

echo "🏗  Rebuilding Milimo Quantum Docker Images..."

max_retries=3
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if docker-compose build --no-cache; then
        echo "✅ Docker build succeeded."
        break
    else
        retry_count=$((retry_count + 1))
        echo "⚠️  Docker build failed (attempt $retry_count/$max_retries). Retrying in 10 seconds..."
        sleep 10
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ Docker build failed after $max_retries attempts. Exiting."
    exit 1
fi

echo ""
echo "⚛  Starting Milimo Quantum Docker Cluster (Infrastructure + Frontend Only)..."
VITE_API_URL=http://host.docker.internal:8000 docker compose --profile dev up -d postgres redis neo4j keycloak celery_worker frontend --force-recreate

echo ""
echo "   Frontend: http://localhost:5173"
echo "   Neo4j:    http://localhost:7474"
echo "   Keycloak: http://localhost:8080"
echo "   Postgres: localhost:5432"
echo "   Redis:    localhost:6379"
echo "   Celery Worker is running in background"
echo ""
echo "Now run './start-backend-mlx.sh' to start the Apple Silicon native backend!"
echo "Use './logs-docker.sh' to view logs."
