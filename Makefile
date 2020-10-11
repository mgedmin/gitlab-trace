.PHONY: test
test:                           ##: run tests
	tox -p auto

.PHONY: check
check:
# 'make check' is defined in release.mk and here's how you can override it
define check_recipe =
	TOX_SKIP_ENV=check-manifest tox -p auto
endef

.PHONY: coverage
coverage:                       ##: measure test coverage
	tox -e $@

.PHONY: mypy
mypy:                           ##: check for type problems
	tox -e $@

.PHONY: flake8
flake8:                         ##: check for style problems
	tox -e $@


FILE_WITH_VERSION = gitlab_trace.py
include release.mk
