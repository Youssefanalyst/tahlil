# Tahlil (PyQt6 Spreadsheet + BI)

Lightweight spreadsheet and BI app built with Python and PyQt6, featuring a safe formula engine, CSV import/export, JSON save/load, basic charts, and a simple Pivot (sum) view.

## Quick Start

- Python ≥ 3.10
- Linux (tested on Linux)

### Setup

```bash
python3 -m venv .venv
bash -lc '. .venv/bin/activate && pip install -r requirements.txt'
```

### Run

```bash
bash -lc '. .venv/bin/activate && python main.py'
```

## Features

- Multi-sheet workbooks via tabs.
- Safe formula engine (no arbitrary Python execution).
  - Examples: `=1+2*3`, `=SUM(1, 2, 3)`, `=AVG(CELL("A1"), CELL("B2"))`, `=ROUND(PI, 2)`
  - Cell references: `=A1 + B2`, or `=SUM(A1, A2, B2)`.
- CSV import/export.
- Save/open workbook as JSON.
- Basic charts (Line/Bar/Scatter) from selection.
- Simple Pivot (Sum) from selection.

## Usage

- From the File menu:
  - New Sheet: create a new sheet.
  - Open: open a JSON workbook.
  - Save As: save the workbook to JSON.
  - Import CSV / Export CSV: import/export CSV for the current sheet.
- From the BI menu:
  - Chart from Selection: select a contiguous cell range (ideally first row as headers), then chart.
  - Pivot (Sum) from Selection: uses the first column as the GroupBy key, others as numeric columns.

## Project Structure

- `main.py`: application entry point.
- `tahlil/core/formula.py`: safe formula engine.
- `tahlil/core/workbook.py`: workbook and sheets management.
- `tahlil/models/sheet_model.py`: table model and formula handling.
- `tahlil/ui/main_window.py`: main window and menus.
- `tahlil/ui/sheet_view.py`: grid view settings.
- `tahlil/ui/chart_dialog.py`: chart dialog using Matplotlib.
- `tahlil/io/csv_io.py`: CSV import/export.
- `tahlil/io/json_io.py`: JSON save/load.

## Security Notes

- No open `eval`; formulas are parsed via AST with a limited, whitelisted set of operations and functions.
- No file or network access is possible from formulas.
- Numeric conversions are guarded and constrained.

## Artificial Intelligence (RAG)

- A standalone RAG agent is located in the `agents/rag_agent/` path.
- To set up:
  - `python -m venv .rag-venv && . .rag-venv/bin/activate && pip install -r agents/rag_agent/requirements.txt`
  - Build the index: `python agents/rag_agent/ingest.py tahlil agents/rag_agent/README.md`
  - Query: `OPENROUTER_API_KEY=sk-or-... python agents/rag_agent/query.py -q "your question"`
- Within the app: from the `AI -> Ask AI (RAG)...` menu, and you can pass the selected range as Context automatically.

## Repository Structure

- `tahlil/` application code (Core/Models/UI/IO).
- `agents/rag_agent/` RAG agent (FAISS + LangChain) with separate `requirements.txt`.
- `requirements.txt` application dependencies.
- `LICENSE` project license (MIT).
- `.gitignore` and `.gitattributes` for repository cleanup.

## Publish to GitHub

1) Initialize Git and create the first commit:
```bash
git init
git add .
git commit -m "Initial commit: Tahlil app with RAG agent"
```

2) Create a new repository on GitHub, then add remote and push:
```bash
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

## Notes
- Do not commit secrets. Use `OPENROUTER_API_KEY` environment variable.
- The folder `agents/rag_agent/store/` is ignored by Git (vector indexes are built locally).

## Future Ideas

- Support ranges like `A1:B10` in functions.
- More statistical functions.
- Advanced cell formatting tools.
- Advanced Pivot editor with column pickers.
