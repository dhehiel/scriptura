
# Scriptura build and verification entry points.
#
# make check runs every repository check. make test runs the full suite.
# Both must exit zero before work is reported complete (AGENTS.md section 8).

PYTHON ?= python3
export PYTHONPATH := src:$(PYTHONPATH)

.PHONY: check test check-docs check-licences check-schemas db clean help

help:
	@echo "make check          - all repository checks (structure, hygiene, licences, docs, schemas)"
	@echo "make test           - full test suite under stdlib unittest"
	@echo "make check-docs     - documentation integrity only"
	@echo "make check-licences - registry/manifest consistency + licence gate only"
	@echo "make check-schemas  - schema validity + registry conformance only"
	@echo "make db DB=path     - build an empty knowledge base at path"
	@echo "make clean          - remove local caches (never touches the repo)"

check:
	$(PYTHON) tools/check_repo.py

test:
	$(PYTHON) -m unittest discover -s tests -v

check-docs:
	$(PYTHON) tools/check_docs.py

check-licences:
	$(PYTHON) tools/check_licences.py

check-schemas:
	$(PYTHON) tools/check_schemas.py

db:
	@test -n "$(DB)" || (echo "usage: make db DB=/tmp/scriptura.db" && exit 1)
	$(PYTHON) tools/build_db.py --db "$(DB)"

clean:
	find . -path ./.git -prune -o -path ./.cline-home -prune -o -name '__pycache__' -print | xargs rm -rf
	find . -path ./.git -prune -o -name '*.pyc' -print -delete
	@echo "clean (caches only; no repository content touched)"

# Scriptura build and verification entry points.
