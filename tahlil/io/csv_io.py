from __future__ import annotations
import csv
from typing import List
from PyQt6.QtCore import Qt
from tahlil.models.sheet_model import SheetModel


def import_csv_to_model(path: str, model: SheetModel) -> None:
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows: List[List[str]] = [row for row in reader]
    max_cols = max((len(r) for r in rows), default=0)
    model.ensure_size(len(rows), max_cols)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            idx = model.index(r, c)
            model.setData(idx, cell, Qt.ItemDataRole.EditRole)


def export_model_to_csv(path: str, model: SheetModel) -> None:
    rows = model.rowCount()
    cols = model.columnCount()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in range(rows):
            out = []
            for c in range(cols):
                idx = model.index(r, c)
                raw = model.data(idx, Qt.ItemDataRole.EditRole)
                out.append("" if raw is None else str(raw))
            writer.writerow(out)
