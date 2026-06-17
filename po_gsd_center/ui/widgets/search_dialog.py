from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from ...utils.search import query as search_query
from ...models.entities import SearchResult

ICONS = {
    "task": "✅",
    "note": "📝",
    "deadline": "📅",
    "link": "🔗",
    "idea": "💡",
    "snippet": "⌨",
}


class SearchDialog(QDialog):
    result_selected = pyqtSignal(str, str, str)  # entity_type, project_id, entity_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMaximumWidth(680)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search tasks, notes, deadlines, ideas…")
        self._search_input.setFixedHeight(40)
        self._search_input.setStyleSheet("font-size: 15px; border-radius: 8px; padding: 0 12px;")
        self._search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._search_input)

        self._list = QListWidget()
        self._list.setFixedHeight(320)
        self._list.itemActivated.connect(self._on_activated)
        self._list.setStyleSheet("border: none;")
        layout.addWidget(self._list)

        hint = QLabel("↑↓ navigate  •  Enter to open  •  Esc to close")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._run_search)
        self._results: list[SearchResult] = []

    def showEvent(self, event):
        super().showEvent(event)
        self._search_input.setFocus()
        self._search_input.clear()
        self._list.clear()
        # Center over parent
        if self.parent():
            p = self.parent()
            x = p.x() + (p.width() - self.width()) // 2
            y = p.y() + (p.height() - self.height()) // 3
            self.move(x, y)

    def _on_text_changed(self, text: str) -> None:
        self._timer.start(150)

    def _run_search(self) -> None:
        term = self._search_input.text().strip()
        self._list.clear()
        self._results = []
        if not term:
            return
        self._results = search_query(term, limit=20)
        for r in self._results:
            icon = ICONS.get(r.entity_type, "•")
            item = QListWidgetItem(f"  {icon}  {r.title}")
            item.setToolTip(f"{r.entity_type} · {r.body[:80]}" if r.body else r.entity_type)
            self._list.addItem(item)
        if self._results:
            self._list.setCurrentRow(0)

    def _on_activated(self, item: QListWidgetItem) -> None:
        idx = self._list.row(item)
        if 0 <= idx < len(self._results):
            r = self._results[idx]
            self.result_selected.emit(r.entity_type, r.project_id, r.entity_id)
            self.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            current = self._list.currentItem()
            if current:
                self._on_activated(current)
        elif key == Qt.Key.Key_Down:
            row = self._list.currentRow()
            if row < self._list.count() - 1:
                self._list.setCurrentRow(row + 1)
        elif key == Qt.Key.Key_Up:
            row = self._list.currentRow()
            if row > 0:
                self._list.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)
