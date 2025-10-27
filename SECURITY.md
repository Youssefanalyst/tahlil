# Security Policy

## API Keys and Secrets
- Never commit API keys to the repository. The app and RAG agent read `OPENROUTER_API_KEY` from the environment.
- The UI provides an optional "Remember key" checkbox. This stores the key in OS `QSettings` as plaintext. Use only on trusted machines.
- Prefer exporting the key per-session:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

## Local Vector Index
- FAISS index is saved under `agents/rag_agent/store/` and is excluded from Git by `.gitignore`.
- The index may contain chunks of your documents. Treat the folder as sensitive if your documents are sensitive.

## Dependencies
- Use project-specific virtual environments.
  - App UI: `.venv`
  - RAG agent: `.rag-venv`
- Keep dependencies updated to receive security patches.

## Reporting
If you discover a vulnerability or security issue, please open a private report to the maintainer instead of a public issue. Provide steps to reproduce, affected versions, and any proposed mitigations.
