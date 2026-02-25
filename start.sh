#!/bin/bash
# Milimo Quantum — Start Both Services
DIR="$(dirname "$0")"

echo "⚛  Starting Milimo Quantum..."
echo ""

# Start backend in background
echo "🔧 Starting Backend (port 8000)..."
cd "$DIR/backend"
source milimoenv/bin/activate
python run.py &
BACKEND_PID=$!

# Start frontend in background
echo "🎨 Starting Frontend (port 5173)..."
cd "$DIR/frontend"
npx vite --port 5173 --host &
FRONTEND_PID=$!

echo ""
echo "⚛  Milimo Quantum is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services."

# Trap Ctrl+C to kill both
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
