#!/bin/bash
# Milimo Quantum — Start Docker Cluster
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "⚛  Starting Milimo Quantum Docker Cluster..."
docker compose --profile dev up -d

echo ""
echo "⚛  Cluster is running in the background!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   Neo4j:    http://localhost:7474"
echo "   Keycloak: http://localhost:8080"
echo ""
echo "Use './logs-docker.sh' to view logs or './stop-docker.sh' to stop the cluster."
