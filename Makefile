.PHONY: help
help:
	@echo "make test        run tests"
	@echo "make coverage    measure test coverage"
	@echo "make release     publish a new release to PyPI"

.PHONY: test
test:
	tox -p auto

.PHONY: check
check:
	TOX_SKIP_ENV=check-manifest tox -p auto

.PHONY: coverage
coverage:
	tox -e coverage

include release.mk
