# RAG Agent (LangChain + OpenRouter Minimax)

This folder contains a minimal, secure RAG pipeline to ingest your data and ask questions using LangChain and OpenRouter (model: `minimax/minimax-m2:free`).

## Setup

1. Create a virtualenv (recommended) and install requirements:

```bash
python -m venv .rag-venv
. .rag-venv/bin/activate
pip install -r agents/rag_agent/requirements.txt
```

2. Export your OpenRouter API key (never hardcode it):

```bash
export OPENROUTER_API_KEY="sk-or-..."
# Optional overrides
export LLM_MODEL="minimax/minimax-m2:free"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

3. Ingest your data (files or folders of .txt/.md/.py, etc.):

```bash
python agents/rag_agent/ingest.py docs/ README.md
```

4. Ask questions:

```bash
python agents/rag_agent/query.py -q "Ask your question here"
```

Examples:

```bash
# Basic question
python agents/rag_agent/query.py -q "Explain the Tahlil project and its components"

# With extra context (e.g., selected cells CSV passed from UI)
python agents/rag_agent/query.py -q "Compute the average" --extra "column1,column2\n10,20\n30,40"
```

## Notes
- Uses FAISS locally for vector search; index is saved under `agents/rag_agent/store/faiss_index`.
- Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings to avoid external embedding APIs.
- Secure by design: reads API key from `OPENROUTER_API_KEY`, maps to OpenAI-compatible env vars.
- To change chunking/retrieval parameters, set env vars: `CHUNK_SIZE`, `CHUNK_OVERLAP`, `K_RETRIEVAL`.

## UI Integration

Inside the main app, open `AI -> Ask AI (RAG)...` dialog. If a cell range is selected, the app passes it as CSV to the agent via `--extra` automatically.
