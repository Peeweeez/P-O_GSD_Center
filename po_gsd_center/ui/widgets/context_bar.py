from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class ContextBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setObjectName("context_bar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        self._color_dot = QLabel("●")
        self._color_dot.setStyleSheet("font-size: 16px;")
        layout.addWidget(self._color_dot)

        self._name = QLabel()
        self._name.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self._name)

        self._status = QLabel()
        self._status.setStyleSheet("font-size: 11px; border: 1px solid #ccc; border-radius: 4px; padding: 1px 6px;")
        layout.addWidget(self._status)

        self._open = QLabel()
        self._open.setObjectName("muted")
        layout.addWidget(self._open)

        self._overdue = QLabel()
        self._overdue.setStyleSheet("color: #ef4444; font-size: 12px;")
        layout.addWidget(self._overdue)

        layout.addStretch()

        self._progress = QProgressBar()
        self._progress.setFixedWidth(120)
        self._progress.setFixedHeight(8)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress)

        self._pct = QLabel("0%")
        self._pct.setObjectName("muted")
        self._pct.setFixedWidth(36)
        layout.addWidget(self._pct)

    def update_project(self, project, stats: dict) -> None:
        self._color_dot.setStyleSheet(f"font-size: 16px; color: {project.color};")
        self._name.setText(project.name)
        self._status.setText(project.status)
        self._open.setText(f"{stats['open']} open")
        if stats["overdue"] > 0:
            self._overdue.setText(f"⚠ {stats['overdue']} overdue")
            self._overdue.show()
        else:
            self._overdue.hide()
        pct = stats["completion"]
        self._progress.setValue(pct)
        self._pct.setText(f"{pct}%")

    def clear(self) -> None:
        self._name.setText("")
        self._status.setText("")
        self._open.setText("")
        self._overdue.hide()
        self._progress.setValue(0)
        self._pct.setText("")
        self._color_dot.setStyleSheet("font-size: 16px;")
