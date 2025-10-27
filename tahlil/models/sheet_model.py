from __future__ import annotations
import re
from typing import Any, Dict, Tuple
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from tahlil.core.formula import evaluate_expression


class SheetModel(QAbstractTableModel):
    def __init__(self, rows: int = 100, cols: int = 26, parent=None):
        super().__init__(parent)
        self._rows = rows
        self._cols = cols
        self._data: Dict[Tuple[int, int], Any] = {}
        self._eval_stack: set[str] = set()

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return 0 if parent and parent.isValid() else self._rows

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return 0 if parent and parent.isValid() else self._cols

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:  # type: ignore[override]
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        raw = self._data.get((r, c))
        if role == Qt.ItemDataRole.EditRole:
            return "" if raw is None else raw
        if role == Qt.ItemDataRole.DisplayRole:
            if raw is None:
                return None
            if isinstance(raw, str) and raw.startswith("="):
                addr = self.index_to_address(r, c)
                try:
                    self._eval_stack.add(addr)
                    val = evaluate_expression(
                        raw[1:],
                        lambda a: self.value_at_address(a),
                    )
                except RecursionError:
                    val = "#CYCLE!"
                except NameError:
                    val = "#NAME?"
                except SyntaxError:
                    val = "#SYNTAX"
                except ZeroDivisionError:
                    val = "#DIV/0!"
                except ValueError:
                    val = "#VALUE!"
                except TypeError:
                    val = "#TYPE!"
                except Exception:
                    val = "#ERR"
                finally:
                    self._eval_stack.discard(addr)
                return val
            return raw
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:  # type: ignore[override]
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        r, c = index.row(), index.column()
        v = self._parse_input(value)
        if v is None:
            if (r, c) in self._data:
                del self._data[(r, c)]
        else:
            self._data[(r, c)] = v
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        return True

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):  # type: ignore[override]
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.col_to_name(section)
        return str(section + 1)

    def ensure_size(self, rows: int, cols: int) -> None:
        rows = max(rows, 1)
        cols = max(cols, 1)
        if rows == self._rows and cols == self._cols:
            return
        self.beginResetModel()
        self._rows = max(self._rows, rows)
        self._cols = max(self._cols, cols)
        self.endResetModel()

    def clear(self) -> None:
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()

    def non_empty_cells(self) -> Dict[Tuple[int, int], Any]:
        return dict(self._data)

    def set_cell_raw(self, row: int, col: int, value: Any) -> None:
        idx = self.index(row, col)
        self.setData(idx, value, Qt.ItemDataRole.EditRole)

    def value_at(self, row: int, col: int) -> Any:
        raw = self._data.get((row, col))
        if raw is None:
            return None
        if isinstance(raw, str) and raw.startswith("="):
            addr = self.index_to_address(row, col)
            if addr in self._eval_stack:
                raise RecursionError("cycle")
            try:
                self._eval_stack.add(addr)
                val = evaluate_expression(
                    raw[1:],
                    lambda a: self.value_at_address(a),
                )
            finally:
                self._eval_stack.discard(addr)
            return val
        return raw

    def value_at_address(self, address: str) -> Any:
        r, c = self.address_to_index(address)
        return self.value_at(r, c)

    @staticmethod
    def _parse_input(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        s = str(value).strip()
        if s == "":
            return None
        if s.startswith("="):
            if s.startswith("=="):
                s = "=" + s[2:]
            return s
        if re.fullmatch(r"[-+]?\d+", s):
            try:
                return int(s)
            except Exception:
                return s
        if re.fullmatch(r"[-+]?\d*\.\d+", s):
            try:
                return float(s)
            except Exception:
                return s
        return s

    @staticmethod
    def col_to_name(col: int) -> str:
        n = col + 1
        out = []
        while n:
            n, rem = divmod(n - 1, 26)
            out.append(chr(ord('A') + rem))
        return ''.join(reversed(out))

    @staticmethod
    def name_to_col(name: str) -> int:
        n = 0
        for ch in name.upper():
            if not ('A' <= ch <= 'Z'):
                raise ValueError("bad column")
            n = n * 26 + (ord(ch) - ord('A') + 1)
        return n - 1

    @classmethod
    def address_to_index(cls, addr: str) -> Tuple[int, int]:
        m = re.fullmatch(r"([A-Za-z]{1,3})(\d{1,6})", addr.strip())
        if not m:
            raise ValueError("bad address")
        col = cls.name_to_col(m.group(1))
        row = int(m.group(2)) - 1
        if row < 0 or col < 0:
            raise ValueError("bad address")
        return row, col

    @classmethod
    def index_to_address(cls, row: int, col: int) -> str:
        return f"{cls.col_to_name(col)}{row + 1}"
