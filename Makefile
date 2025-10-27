.PHONY: help install run rag-setup rag-ingest rag-query clean

help:
	@echo "Targets: install, run, rag-setup, rag-ingest PATHS=..., rag-query Q=... [EXTRA=...]"

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && python main.py

rag-setup:
	python3 -m venv .rag-venv
	. .rag-venv/bin/activate && python -m pip install --upgrade pip && pip install -r agents/rag_agent/requirements.txt

rag-ingest:
	. .rag-venv/bin/activate && python agents/rag_agent/ingest.py $(PATHS)

rag-query:
	. .rag-venv/bin/activate && OPENROUTER_API_KEY="$(OPENROUTER_API_KEY)" python agents/rag_agent/query.py -q "$(Q)" --extra "$(EXTRA)"

clean:
	rm -rf **/__pycache__ .pytest_cache .mypy_cache
