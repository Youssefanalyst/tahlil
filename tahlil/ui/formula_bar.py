from __future__ import annotations
from typing import Optional
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QToolButton, QMenu
from tahlil.models.sheet_model import SheetModel
from tahlil.ui.sheet_view import SheetView


class FormulaBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._view: Optional[SheetView] = None
        self._current: Optional[QModelIndex] = None

        self.lbl_addr = QLabel("-")
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("=SUM(A1:B2)")
        self.edit.returnPressed.connect(self._apply)

        self.btn_fx = QToolButton()
        self.btn_fx.setText("fx")
        self.btn_fx.setPopupMode(self.btn_fx.ToolButtonPopupMode.InstantPopup)
        self.btn_fx.setMenu(self._build_fx_menu())

        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(8)
        lay.addWidget(self.lbl_addr)
        lay.addWidget(self.edit, 1)
        lay.addWidget(self.btn_fx)

    def _build_fx_menu(self) -> QMenu:
        m = QMenu(self)
        for name in ["SUM()", "AVG()", "AVERAGE()", "MIN()", "MAX()", "IF( , , )", "ROUND( , )", "ABS()"]:
            act = m.addAction(name)
            act.triggered.connect(lambda _, t=name: self._insert_text(t))
        return m

    def _insert_text(self, text: str) -> None:
        cursor = self.edit.cursorPosition()
        s = self.edit.text()
        s = s[:cursor] + text + s[cursor:]
        self.edit.setText(s)
        if text.endswith("()"):
            self.edit.setCursorPosition(cursor + len(text) - 1)
        elif text.endswith(")"):
            self.edit.setCursorPosition(cursor + text.find("(") + 1)
        else:
            self.edit.setCursorPosition(cursor + len(text))

    def set_view(self, view: Optional[SheetView]) -> None:
        if self._view is view:
            return
        if self._view is not None and self._view.selectionModel() is not None:
            try:
                self._view.selectionModel().currentChanged.disconnect(self._on_current_changed)
            except Exception:
                pass
        self._view = view
        if self._view is not None and self._view.selectionModel() is not None:
            self._view.selectionModel().currentChanged.connect(self._on_current_changed)
        self._refresh_from_current()

    def _on_current_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        self._current = current if current.isValid() else None
        self._refresh_from_current()

    def _refresh_from_current(self) -> None:
        if self._view is None:
            self.lbl_addr.setText("-")
            self.edit.setText("")
            return
        sel = self._view.selectionModel()
        idx = None
        if sel is not None:
            idx = sel.currentIndex()
        if idx is None or not idx.isValid():
            idx = self._view.currentIndex()
        if idx is None or not idx.isValid():
            self.lbl_addr.setText("-")
            self.edit.setText("")
            return
        model = self._view.model()
        if not isinstance(model, SheetModel):
            self.lbl_addr.setText("-")
            self.edit.setText("")
            return
        addr = SheetModel.index_to_address(idx.row(), idx.column())
        self.lbl_addr.setText(addr)
        raw = model.data(idx, role=Qt.ItemDataRole.EditRole)
        self.edit.setText("" if raw is None else str(raw))

    def _apply(self) -> None:
        if self._view is None:
            return
        sel = self._view.selectionModel()
        idx = None
        if sel is not None:
            idx = sel.currentIndex()
        if idx is None or not idx.isValid():
            idx = self._view.currentIndex()
        if idx is None or not idx.isValid():
            return
        model = self._view.model()
        if not isinstance(model, SheetModel):
            return
        model.setData(idx, self.edit.text(), role=Qt.ItemDataRole.EditRole)
        self._refresh_from_current()
