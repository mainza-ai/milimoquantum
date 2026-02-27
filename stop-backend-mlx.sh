#!/bin/bash
# Milimo Quantum — Stop Native Apple Silicon Backend
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "🛑 Stopping Native Apple Silicon Backend (port 8000)..."

# Find PIDs for port 8000 and run.py
PORT_PIDS=$(lsof -t -i:8000 2>/dev/null)
RUN_PIDS=$(pgrep -f "python run.py" 2>/dev/null)

# Combine and deduplicate PIDs
ALL_PIDS=$(echo "$PORT_PIDS $RUN_PIDS" | tr ' ' '\n' | sort -u | grep -v '^$')

if [ -z "$ALL_PIDS" ]; then
    echo "   No backend process found running."
else
    # Output multiple PIDs on one line for cleaner logs
    PID_LIST=$(echo $ALL_PIDS | tr '\n' ' ')
    echo "   Sending graceful termination to processes: $PID_LIST"
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $ALL_PIDS 2>/dev/null
    
    # Wait for up to 5 seconds for them to exit gracefully
    for i in {1..5}; do
        if kill -0 $ALL_PIDS 2>/dev/null; then
            sleep 1
        else
            break
        fi
    done
    
    # Force kill any remaining processes
    if kill -0 $ALL_PIDS 2>/dev/null; then
        echo "   Force killing remaining processes..."
        kill -9 $ALL_PIDS 2>/dev/null
    fi
    echo "   Backend stopped gracefully."
fi

echo ""
echo "🛑 MLX Backend has been successfully shut down."
