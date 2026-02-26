#!/bin/bash
# Milimo Quantum — Stop Docker Cluster
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "🛑 Stopping Milimo Quantum Docker Cluster..."
docker compose down

echo ""
echo "🛑 Cluster stopped successfully."
