#!/bin/bash
# Milimo Quantum — Start Frontend
cd "$(dirname "$0")/frontend"
echo "⚛  Starting Milimo Quantum Frontend..."
npx vite --port 5173 --host
