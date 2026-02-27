#!/bin/bash
# Milimo Quantum — Start Docker Cluster (No Backend) for MLX Native
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "⚛  Starting Milimo Quantum Docker Cluster (Infrastructure + Frontend Only)..."
# For the local frontend to proxy requests correctly to the Mac Host MLX Backend, 
# we override the default Docker-internal backend URL.
VITE_API_URL=http://host.docker.internal:8000 docker compose --profile dev up -d postgres redis neo4j keycloak celery_worker frontend

echo ""
echo "⚛  Cluster infrastructure is running in the background!"
echo "   Frontend: http://localhost:5173"
echo "   Neo4j:    http://localhost:7474"
echo "   Keycloak: http://localhost:8080"
echo "   Postgres: localhost:5432"
echo "   Redis:    localhost:6379"
echo "   Celery Worker is running in background"
echo ""
echo "Now run './start-backend-mlx.sh' to start the Apple Silicon native backend!"
