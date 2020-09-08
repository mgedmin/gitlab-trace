.PHONY: help
help:
	@echo "make test        run tests"
	@echo "make coverage    measure test coverage"

.PHONY: test check
test check:
	tox -p auto

.PHONY: coverage
coverage:
	tox -e coverage
