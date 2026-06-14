.PHONY: format lint type-check test check

format:
	isort backend
	black backend

lint:
	pylint backend --recursive=y --ignore=tests

type-check:
	mypy backend

test:
	pytest backend/tests -v

check: format lint type-check test
