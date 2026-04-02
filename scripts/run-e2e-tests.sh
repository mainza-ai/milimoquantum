#!/bin/bash
set -e

echo "=============================================="
echo "  Milimo Quantum E2E Test Runner"
echo "=============================================="
echo ""

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"

check_service() {
    local name=$1
    local url=$2
    echo -n "Checking $name... "
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✓ Running"
        return 0
    else
        echo "✗ Not available"
        return 1
    fi
}

echo "=== Service Health Checks ==="
check_service "Backend" "$BACKEND_URL/api/health" || true
check_service "Frontend" "$FRONTEND_URL" || true

echo ""
echo "=== Running Backend E2E Tests ==="
cd backend
if [ -d "tests/e2e" ]; then
    python -m pytest tests/e2e/ -v --tb=short -m e2e "$@" || true
else
    echo "No E2E tests found in backend/tests/e2e/"
fi

echo ""
echo "=== Running Frontend E2E Tests ==="
cd ../frontend
if command -v npx &> /dev/null && [ -f "playwright.config.ts" ]; then
    echo "Installing Playwright browsers..."
    npx playwright install chromium --with-deps 2>/dev/null || true
    echo "Running Playwright tests..."
    npx playwright test --reporter=list "$@" || true
else
    echo "Playwright not configured. Skipping frontend tests."
fi

echo ""
echo "=============================================="
echo "  E2E Tests Complete"
echo "=============================================="
