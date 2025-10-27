import sys
from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication
from tahlil.ui.main_window import MainWindow
from tahlil.ui.theme_manager import apply_saved_theme


def main() -> int:
    QCoreApplication.setOrganizationName("Tahlil")
    QCoreApplication.setApplicationName("Tahlil")
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
    apply_saved_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
