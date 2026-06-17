import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont

from .db.connection import init_db
from .app_state import AppState
from .ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("P-O GSD Center")
    app.setOrganizationName("P-O")

    # Try to load DM Sans if bundled; otherwise fall back to system font
    font_loaded = QFontDatabase.addApplicationFont(":/fonts/DMSans.ttf")
    if font_loaded == -1:
        font = QFont("Segoe UI", 10)
        app.setFont(font)
    else:
        families = QFontDatabase.applicationFontFamilies(font_loaded)
        if families:
            app.setFont(QFont(families[0], 10))

    init_db()
    state = AppState()
    window = MainWindow(state)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
