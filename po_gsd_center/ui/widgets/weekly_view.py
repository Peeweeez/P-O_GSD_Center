from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from ...db.repositories import task_repo
from ...utils.dates import week_dates, today_str
from ...models.entities import Task
from datetime import date


class DayColumn(QFrame):
    task_clicked = pyqtSignal(str)

    def __init__(self, day: date, tasks: list[Task], is_today: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        day_name = day.strftime("%a")
        day_num = day.strftime("%d")
        month = day.strftime("%b")

        header = QLabel(f"{day_name}\n{month} {day_num}")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_today:
            header.setStyleSheet("background-color: #3d6b8c; color: white; border-radius: 6px; padding: 4px;")
        else:
            header.setStyleSheet("font-weight: bold; color: #6b7280;")
        layout.addWidget(header)

        for t in tasks:
            chip = QPushButton(t.title[:24] + ("…" if len(t.title) > 24 else ""))
            chip.setFixedHeight(28)
            chip.setStyleSheet(self._chip_style(t))
            chip.setToolTip(t.title)
            tid = t.id
            chip.clicked.connect(lambda _, task_id=tid: self.task_clicked.emit(task_id))
            layout.addWidget(chip)

        if not tasks:
            empty = QLabel("—")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)

        layout.addStretch()

    @staticmethod
    def _chip_style(t: Task) -> str:
        colors = {
            "critical": ("#fee2e2", "#b91c1c"),
            "high":     ("#fef3c7", "#92400e"),
            "medium":   ("#dbeafe", "#1e40af"),
            "low":      ("#f3f4f6", "#374151"),
        }
        bg, fg = colors.get(t.priority, ("#f3f4f6", "#374151"))
        text_dec = "line-through" if t.status == "done" else "none"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-radius: 4px;
                padding: 2px 6px;
                text-align: left;
                text-decoration: {text_dec};
                font-size: 11px;
            }}
            QPushButton:hover {{ opacity: 0.8; }}
        """


class WeeklyView(QWidget):
    task_edit_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Weekly View")
        title.setObjectName("section_title")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._cols_layout = QHBoxLayout(self._content)
        self._cols_layout.setSpacing(8)
        self._cols_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def refresh(self) -> None:
        # Clear existing columns
        while self._cols_layout.count():
            child = self._cols_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._project_id:
            return

        today = today_str()
        days = week_dates()
        for day in days:
            day_str = day.isoformat()
            tasks = task_repo.get_for_date(self._project_id, day_str)
            col = DayColumn(day, tasks, day_str == today)
            col.task_clicked.connect(self.task_edit_requested)
            self._cols_layout.addWidget(col)
        self._cols_layout.addStretch()
