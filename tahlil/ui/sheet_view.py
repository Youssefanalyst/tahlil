from PyQt6.QtWidgets import QTableView
from PyQt6.QtCore import Qt


class SheetView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QTableView.EditTrigger.DoubleClicked | QTableView.EditTrigger.EditKeyPressed | QTableView.EditTrigger.AnyKeyPressed)
        self.horizontalHeader().setStretchLastSection(False)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setDefaultSectionSize(80)
        self.setCornerButtonEnabled(False)
        self.setSortingEnabled(False)
        self.setWordWrap(False)
        self.setTabKeyNavigation(True)
