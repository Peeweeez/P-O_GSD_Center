from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class Topbar(QWidget):
    search_requested = pyqtSignal()
    export_requested = pyqtSignal()
    import_requested = pyqtSignal()
    dark_mode_toggled = pyqtSignal()
    new_project_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        self._title = QLabel("Overview")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self._title.setFont(font)
        layout.addWidget(self._title)
        layout.addStretch()

        search_btn = QPushButton("🔍  Search  (Ctrl+K)")
        search_btn.setObjectName("icon_btn")
        search_btn.setFixedHeight(32)
        search_btn.setStyleSheet("padding: 0 10px; border: 1px solid #d1d5db; border-radius: 6px;")
        search_btn.clicked.connect(self.search_requested)
        layout.addWidget(search_btn)

        new_proj_btn = QPushButton("＋ Project")
        new_proj_btn.setObjectName("primary")
        new_proj_btn.setFixedHeight(32)
        new_proj_btn.clicked.connect(self.new_project_requested)
        layout.addWidget(new_proj_btn)

        export_btn = QPushButton("⬆ Export")
        export_btn.setObjectName("icon_btn")
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self.export_requested)
        layout.addWidget(export_btn)

        import_btn = QPushButton("⬇ Import")
        import_btn.setObjectName("icon_btn")
        import_btn.setFixedHeight(32)
        import_btn.clicked.connect(self.import_requested)
        layout.addWidget(import_btn)

        self._dark_btn = QPushButton("🌙")
        self._dark_btn.setObjectName("icon_btn")
        self._dark_btn.setFixedSize(32, 32)
        self._dark_btn.setToolTip("Toggle dark mode")
        self._dark_btn.clicked.connect(self.dark_mode_toggled)
        layout.addWidget(self._dark_btn)

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_dark(self, dark: bool) -> None:
        self._dark_btn.setText("☀" if dark else "🌙")
