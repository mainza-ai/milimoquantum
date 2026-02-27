#!/bin/bash
# Milimo Quantum — Rebuild & Start Docker Cluster
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "🏗  Rebuilding Milimo Quantum Docker Images..."
docker compose --profile dev build --no-cache

echo ""
echo "⚛  Starting Milimo Quantum Docker Cluster..."
docker compose --profile dev up -d --force-recreate

echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   Neo4j:    http://localhost:7474"
echo "   Keycloak: http://localhost:8080"
echo "   Postgres: localhost:5432"
echo "   Redis:    localhost:6379"
echo "   Celery Worker is running in background"
echo ""
echo "Use './logs-docker.sh' to view logs."
