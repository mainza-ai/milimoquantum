#!/bin/bash
# Milimo Quantum — Start Backend
cd "$(dirname "$0")/backend"
source milimoenv/bin/activate
echo "⚛  Starting Milimo Quantum Backend..."
python run.py
