from __future__ import annotations
from typing import List
import pandas as pd
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QListWidgetItem, QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ChartDialog(QDialog):
    def __init__(self, df: pd.DataFrame, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chart")
        self.resize(900, 600)
        self._df = df.copy()
        self._figure = Figure(figsize=(5, 4))
        self._canvas = FigureCanvas(self._figure)

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["Line", "Bar", "Scatter"])

        self.cmb_x = QComboBox()
        self.cmb_x.addItems([str(c) for c in self._df.columns])

        self.lst_y = QListWidget()
        self.lst_y.setSelectionMode(self.lst_y.SelectionMode.MultiSelection)
        for c in self._df.columns:
            if c != self._df.columns[0]:
                it = QListWidgetItem(str(c))
                it.setSelected(True)
                self.lst_y.addItem(it)
            else:
                self.lst_y.addItem(QListWidgetItem(str(c)))

        self.btn_plot = QPushButton("Plot")
        self.btn_plot.clicked.connect(self._plot)

        top = QHBoxLayout()
        top.addWidget(QLabel("Type"))
        top.addWidget(self.cmb_type)
        top.addWidget(QLabel("X"))
        top.addWidget(self.cmb_x)
        top.addWidget(QLabel("Y"))
        top.addWidget(self.lst_y)
        top.addWidget(self.btn_plot)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self._canvas)

        self.cmb_type.currentIndexChanged.connect(self._plot)
        self.cmb_x.currentIndexChanged.connect(self._plot)
        self.lst_y.itemSelectionChanged.connect(self._plot)
        self._plot()

    def _plot(self) -> None:
        x_col = self.cmb_x.currentText()
        y_cols = [it.text() for it in self.lst_y.selectedItems()]
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        if not x_col or not y_cols:
            self._canvas.draw()
            return
        try:
            if self.cmb_type.currentText() == "Line":
                for y in y_cols:
                    ax.plot(self._df[x_col], self._df[y], label=str(y))
            elif self.cmb_type.currentText() == "Bar":
                x = self._df[x_col]
                idx = range(len(x))
                w = 0.8 / max(1, len(y_cols))
                for i, y in enumerate(y_cols):
                    offs = [j + i * w for j in idx]
                    ax.bar(offs, self._df[y], width=w, label=str(y))
                ax.set_xticks([j + (len(y_cols)-1)*w/2 for j in idx], [str(v) for v in x])
            else:
                for y in y_cols:
                    ax.scatter(self._df[x_col], self._df[y], label=str(y))
        except Exception:
            pass
        ax.legend(loc="best")
        ax.grid(True)
        self._canvas.draw()
