from __future__ import annotations
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QInputDialog,
    QApplication,
    QWidget,
    QVBoxLayout,
)
from tahlil.core.workbook import Workbook
from tahlil.io.csv_io import export_model_to_csv, import_csv_to_model
from tahlil.io.json_io import load_workbook, save_workbook
from tahlil.models.sheet_model import SheetModel
from tahlil.ui.sheet_view import SheetView
from tahlil.ui.chart_dialog import ChartDialog
from tahlil.ui.theme_manager import (
    get_available_themes,
    get_saved_theme,
    save_theme,
    apply_theme,
)
from tahlil.ui.formula_bar import FormulaBar
from tahlil.ui.ai_dialog import AIDialog
import pandas as pd


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tahlil")
        self.resize(1100, 700)
        self._current_path: Optional[Path] = None
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._on_close_tab)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self._formula = FormulaBar()
        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._formula)
        lay.addWidget(self._tabs, 1)
        self.setCentralWidget(central)
        self._wb = Workbook()
        self._create_actions()
        self._create_menus()
        self._add_new_sheet()

    def _create_actions(self) -> None:
        self.act_new_sheet = QAction("New Sheet", self)
        self.act_new_sheet.triggered.connect(self._add_new_sheet)

        self.act_open = QAction("Open...", self)
        self.act_open.triggered.connect(self._open_workbook)

        self.act_save_as = QAction("Save As...", self)
        self.act_save_as.triggered.connect(self._save_as)

        self.act_import_csv = QAction("Import CSV...", self)
        self.act_import_csv.triggered.connect(self._import_csv)

        self.act_export_csv = QAction("Export CSV...", self)
        self.act_export_csv.triggered.connect(self._export_csv)

        self.act_chart_sel = QAction("Chart from Selection...", self)
        self.act_chart_sel.triggered.connect(self._chart_from_selection)

        self.act_pivot_sel = QAction("Pivot (Sum) from Selection", self)
        self.act_pivot_sel.triggered.connect(self._pivot_from_selection)

        self.act_switch_theme = QAction("Switch Theme...", self)
        self.act_switch_theme.triggered.connect(self._switch_theme)

        self.act_ai_ask = QAction("Ask AI (RAG)...", self)
        self.act_ai_ask.triggered.connect(self._ai_ask)

    def _create_menus(self) -> None:
        m_file = self.menuBar().addMenu("File")
        m_file.addAction(self.act_new_sheet)
        m_file.addSeparator()
        m_file.addAction(self.act_open)
        m_file.addAction(self.act_save_as)
        m_file.addSeparator()
        m_file.addAction(self.act_import_csv)
        m_file.addAction(self.act_export_csv)

        m_bi = self.menuBar().addMenu("BI")
        m_bi.addAction(self.act_chart_sel)
        m_bi.addAction(self.act_pivot_sel)

        m_view = self.menuBar().addMenu("View")
        m_view.addAction(self.act_switch_theme)

        m_ai = self.menuBar().addMenu("AI")
        m_ai.addAction(self.act_ai_ask)

    def _add_new_sheet(self) -> None:
        model = self._wb.add_sheet()
        view = SheetView()
        view.setModel(model)
        name = self._wb.sheets()[-1][0]
        self._tabs.addTab(view, name)
        self._tabs.setCurrentIndex(self._tabs.count() - 1)
        self._bind_formula_to_current()

    def _on_close_tab(self, index: int) -> None:
        if self._tabs.count() <= 1:
            return
        self._wb.remove_sheet(index)
        self._tabs.removeTab(index)

    def _current_model(self) -> Optional[SheetModel]:
        w = self._tabs.currentWidget()
        if isinstance(w, SheetView):
            m = w.model()
            return m if isinstance(m, SheetModel) else None
        return None

    def _open_workbook(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "Tahlil Workbook (*.json)")
        if not path:
            return
        try:
            wb = load_workbook(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")
            return
        self._wb = wb
        self._tabs.clear()
        for name, model in self._wb.sheets():
            view = SheetView()
            view.setModel(model)
            self._tabs.addTab(view, name)
        self._current_path = Path(path)
        self._tabs.setCurrentIndex(0)
        self._bind_formula_to_current()

    def _save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Tahlil Workbook (*.json)")
        if not path:
            return
        try:
            save_workbook(self._wb, path)
            self._current_path = Path(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _import_csv(self) -> None:
        model = self._current_model()
        if model is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            import_csv_to_model(path, model)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import CSV:\n{e}")

    def _export_csv(self) -> None:
        model = self._current_model()
        if model is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            export_model_to_csv(path, model)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV:\n{e}")

    def _current_view(self) -> Optional[SheetView]:
        w = self._tabs.currentWidget()
        return w if isinstance(w, SheetView) else None

    def _selection_to_dataframe(self) -> Optional[pd.DataFrame]:
        view = self._current_view()
        model = self._current_model()
        if view is None or model is None:
            return None
        sel = view.selectionModel()
        if sel is None:
            return None
        idxs = sel.selectedIndexes()
        if not idxs:
            QMessageBox.information(self, "Selection", "Please select a contiguous range of cells.")
            return None
        rows = [i.row() for i in idxs]
        cols = [i.column() for i in idxs]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        data = []
        for r in range(r0, r1 + 1):
            row_vals = []
            for c in range(c0, c1 + 1):
                v = model.value_at(r, c)
                if isinstance(v, (int, float)):
                    row_vals.append(v)
                else:
                    try:
                        fv = float(str(v))
                        row_vals.append(fv)
                    except Exception:
                        row_vals.append(v)
            data.append(row_vals)
        if not data:
            return None
        first_row = data[0]
        has_text_header = any((isinstance(x, str) and str(x).strip() != "") for x in first_row)
        if has_text_header:
            headers = [str(x) if x is not None else "" for x in first_row]
            body = data[1:]
        else:
            headers = [SheetModel.col_to_name(c) for c in range(c0, c1 + 1)]
            body = data
        if not body:
            QMessageBox.information(self, "Selection", "Selected range does not contain enough data.")
            return None
        try:
            df = pd.DataFrame(body, columns=headers)
        except Exception:
            df = pd.DataFrame(body)
        return df

    def _chart_from_selection(self) -> None:
        df = self._selection_to_dataframe()
        if df is None or df.empty:
            return
        dlg = ChartDialog(df, self)
        dlg.exec()

    def _pivot_from_selection(self) -> None:
        df = self._selection_to_dataframe()
        if df is None or df.empty or df.shape[1] < 2:
            QMessageBox.information(self, "Pivot", "Select at least 2 columns and 2 rows.")
            return
        key = df.columns[0]
        value_cols = [c for c in df.columns[1:]]
        try:
            num_df = df[value_cols].apply(pd.to_numeric, errors="coerce")
            pivot = num_df.groupby(df[key]).sum(numeric_only=True).reset_index()
            self._add_sheet_with_dataframe("Pivot", pivot)
        except Exception as e:
            QMessageBox.critical(self, "Pivot", f"Failed to create Pivot:\n{e}")

    def _add_sheet_with_dataframe(self, base_name: str, df: pd.DataFrame) -> None:
        existing = [self._tabs.tabText(i) for i in range(self._tabs.count())]
        name = base_name
        i = 1
        while name in existing:
            i += 1
            name = f"{base_name}{i}"
        model = self._wb.add_sheet(name=name, rows=max(100, len(df) + 10), cols=max(26, len(df.columns) + 5))
        view = SheetView()
        view.setModel(model)
        self._tabs.addTab(view, name)
        self._tabs.setCurrentIndex(self._tabs.count() - 1)
        for c, col in enumerate(df.columns):
            idx = model.index(0, c)
            model.setData(idx, str(col), Qt.ItemDataRole.EditRole)
        for r in range(len(df)):
            for c, col in enumerate(df.columns):
                idx = model.index(r + 1, c)
                val = df.iloc[r, c]
                try:
                    is_na = bool(pd.isna(val))
                except Exception:
                    is_na = False
                model.setData(idx, "" if is_na else val, Qt.ItemDataRole.EditRole)

    def _switch_theme(self) -> None:
        themes = get_available_themes()
        if not themes:
            QMessageBox.information(self, "Themes", "No qt-material themes found.")
            return
        current = get_saved_theme()
        try:
            idx = themes.index(current)
        except ValueError:
            idx = 0
        item, ok = QInputDialog.getItem(self, "Choose Theme", "Theme:", themes, idx, False)
        if not ok or not item:
            return
        app = QApplication.instance()
        if app is None:
            return
        apply_theme(app, item)
        save_theme(item)

    def _on_tab_changed(self, index: int) -> None:
        self._bind_formula_to_current()

    def _bind_formula_to_current(self) -> None:
        view = self._current_view()
        self._formula.set_view(view)

    def _selection_to_text(self) -> str:
        df = self._selection_to_dataframe()
        if df is None or df.empty:
            return ""
        rlim = min(30, df.shape[0])
        clim = min(20, df.shape[1])
        dfx = df.iloc[:rlim, :clim]
        try:
            txt = dfx.to_csv(index=False)
        except Exception:
            txt = "\n".join(
                ",".join(str(x) for x in dfx.iloc[i].tolist()) for i in range(len(dfx))
            )
        name = self._tabs.tabText(self._tabs.currentIndex()) if self._tabs.count() else "Sheet1"
        header = f"Sheet: {name}\nSelected cells (CSV):\n"
        out = header + txt
        if len(out) > 5000:
            out = out[:5000]
        return out

    def _ai_ask(self) -> None:
        dlg = AIDialog(self)
        extra = self._selection_to_text()
        if extra:
            dlg.set_extra_context(extra)
        dlg.exec()
