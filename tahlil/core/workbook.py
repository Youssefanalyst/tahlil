from __future__ import annotations
from typing import List, Tuple
from PyQt6.QtCore import Qt
from tahlil.models.sheet_model import SheetModel


class Workbook:
    def __init__(self) -> None:
        self._sheets: List[Tuple[str, SheetModel]] = []

    def add_sheet(self, name: str | None = None, rows: int = 100, cols: int = 26) -> SheetModel:
        if name is None:
            name = self._next_sheet_name()
        model = SheetModel(rows=rows, cols=cols)
        self._sheets.append((name, model))
        return model

    def remove_sheet(self, index: int) -> None:
        if 0 <= index < len(self._sheets):
            del self._sheets[index]

    def sheet_count(self) -> int:
        return len(self._sheets)

    def sheet(self, index: int) -> Tuple[str, SheetModel]:
        return self._sheets[index]

    def sheets(self) -> List[Tuple[str, SheetModel]]:
        return list(self._sheets)

    def set_sheet_name(self, index: int, name: str) -> None:
        n, m = self._sheets[index]
        self._sheets[index] = (name, m)

    def to_dict(self) -> dict:
        data = {"sheets": []}
        for name, model in self._sheets:
            cells = []
            for (r, c), v in model.non_empty_cells().items():
                cells.append({"r": r, "c": c, "v": v})
            data["sheets"].append(
                {"name": name, "rows": model.rowCount(), "cols": model.columnCount(), "cells": cells}
            )
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Workbook":
        wb = cls()
        for sheet in data.get("sheets", []):
            name = str(sheet.get("name", "Sheet"))
            rows = int(sheet.get("rows", 100))
            cols = int(sheet.get("cols", 26))
            model = wb.add_sheet(name=name, rows=rows, cols=cols)
            for cell in sheet.get("cells", []):
                r = int(cell.get("r", 0))
                c = int(cell.get("c", 0))
                v = cell.get("v", None)
                idx = model.index(r, c)
                model.setData(idx, v, Qt.ItemDataRole.EditRole)
        return wb

    def _next_sheet_name(self) -> str:
        base = "Sheet"
        i = 1
        existing = {n for n, _ in self._sheets}
        while f"{base}{i}" in existing:
            i += 1
        return f"{base}{i}"
