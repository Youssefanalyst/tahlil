from __future__ import annotations
import json
from pathlib import Path
from tahlil.core.workbook import Workbook


def save_workbook(wb: Workbook, path: str) -> None:
    p = Path(path)
    data = wb.to_dict()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_workbook(path: str) -> Workbook:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return Workbook.from_dict(data)
