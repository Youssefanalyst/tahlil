from __future__ import annotations
from typing import List, Optional
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet, list_themes


def get_available_themes() -> List[str]:
    try:
        themes = list_themes()
        return sorted(set(themes))
    except Exception:
        return []


def get_saved_theme() -> str:
    s = QSettings()
    val = s.value("theme", "light_blue.xml", str)
    return val or "light_blue.xml"


def save_theme(theme: str) -> None:
    s = QSettings()
    s.setValue("theme", theme)


def apply_theme(app: QApplication, theme: Optional[str]) -> None:
    t = theme or get_saved_theme()
    try:
        apply_stylesheet(app, theme=t)
    except Exception:
        pass


def apply_saved_theme(app: QApplication) -> None:
    apply_theme(app, get_saved_theme())
