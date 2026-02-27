#!/bin/bash
# Milimo Quantum — Docker Cluster Logs
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "📄 Tailing logs for all services (Press Ctrl+C to exit)..."
docker compose --profile dev logs -f
