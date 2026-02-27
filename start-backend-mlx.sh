#!/bin/bash
# Milimo Quantum — Start Native Apple Silicon Backend
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/backend"

echo "⚛  Activating python environment..."
source milimoenv/bin/activate

echo "⚛  Starting backend with MLX hardware acceleration..."
export LLM_BACKEND=mlx
python run.py
