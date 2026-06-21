#!/usr/bin/env bash
# Run all checks across the whole project: format, lint, type-check, tests.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==================== BACKEND ===================="

echo "=== isort ==="
isort backend --check-only

echo "=== black ==="
black backend --check

echo "=== pylint ==="
pylint backend --recursive=y --ignore=tests

echo "=== mypy ==="
mypy backend

echo "=== pytest ==="
pytest backend/tests -q

# Frontend checks run only if Flutter is installed.
if command -v flutter >/dev/null 2>&1; then
  echo "==================== FRONTEND ===================="
  ( cd frontend && flutter analyze && flutter test )
else
  echo "(Flutter not found — skipping frontend checks)"
fi

echo ""
echo "All checks passed."
