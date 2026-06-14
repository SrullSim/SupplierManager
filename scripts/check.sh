#!/usr/bin/env bash
# Run all checks: format, lint, type-check, tests
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== isort ==="
isort backend --check-only

echo "=== black ==="
black backend --check

echo "=== pylint ==="
pylint backend --recursive=y --ignore=tests

echo "=== mypy ==="
mypy backend

echo "=== pytest ==="
pytest backend/tests -v

echo "All checks passed."
