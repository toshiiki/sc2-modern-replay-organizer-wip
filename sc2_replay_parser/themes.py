"""Theme management for SC2 Replay Organizer GUI."""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


def apply_theme(window: QWidget, dark: bool = True):
    """Apply dark or light theme to the application."""
    app = QApplication.instance()
    if not app:
        return
    
    if dark:
        apply_dark_theme(app)
    else:
        apply_light_theme(app)


def apply_dark_theme(app: QApplication):
    """Apply dark theme to the application."""
    palette = QPalette()
    
    # Dark theme colors
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    
    app.setPalette(palette)


def apply_light_theme(app: QApplication):
    """Apply light theme to the application."""
    app.setPalette(app.style().standardPalette())
