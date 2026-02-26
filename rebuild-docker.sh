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
echo "⚛  Cluster rebuilt and running in the background!"
echo "Use './logs-docker.sh' to view logs."
