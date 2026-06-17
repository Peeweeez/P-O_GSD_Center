from datetime import date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QCalendarWidget, QSplitter, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QPainter, QColor, QTextCharFormat
from ...db.repositories import deadline_repo, task_repo, note_repo
from ...utils.dates import fmt_date_short, today_str


class GSDCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_dates: set[str] = set()
        self._deadline_dates: set[str] = set()
        self._note_dates: set[str] = set()
        self._deadline_ranges: list[tuple] = []  # (start_str, end_str)

        self.setGridVisible(False)
        self.setNavigationBarVisible(True)
        self.setMinimumSize(380, 300)

    def set_events(
        self,
        task_dates: set[str],
        deadline_dates: set[str],
        note_dates: set[str],
        deadline_ranges: list[tuple],
    ) -> None:
        self._task_dates = task_dates
        self._deadline_dates = deadline_dates
        self._note_dates = note_dates
        self._deadline_ranges = deadline_ranges
        self.updateCells()

    def paintCell(self, painter: QPainter, rect, date: QDate) -> None:
        super().paintCell(painter, rect, date)
        date_str = date.toString("yyyy-MM-dd")

        dots_x = rect.x() + 4
        dots_y = rect.bottom() - 6

        dot_colors = []
        if date_str in self._task_dates:
            dot_colors.append(QColor("#3b82f6"))
        if date_str in self._deadline_dates:
            dot_colors.append(QColor("#ef4444"))
        if date_str in self._note_dates:
            dot_colors.append(QColor("#8b5cf6"))

        # Draw range bar for deadlines
        d = date.toPyDate()
        for start_str, end_str in self._deadline_ranges:
            try:
                start = date.fromString(start_str, "yyyy-MM-dd").toPyDate()
                end = date.fromString(end_str, "yyyy-MM-dd").toPyDate()
                if start <= d <= end:
                    painter.fillRect(
                        rect.x(), rect.bottom() - 3, rect.width(), 3,
                        QColor("#ef444466"),
                    )
                    break
            except Exception:
                pass

        for i, color in enumerate(dot_colors):
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dots_x + i * 10, dots_y, 6, 6)


class DeadlineRowWidget(QFrame):
    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    complete_clicked = pyqtSignal(str)

    def __init__(self, deadline, parent=None):
        super().__init__(parent)
        self.deadline = deadline
        self.setObjectName("card")
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        status_lbl = QLabel("✓" if deadline.completed else "📅")
        status_lbl.setFixedWidth(20)
        style = "color: #22c55e;" if deadline.completed else ""
        status_lbl.setStyleSheet(style)
        layout.addWidget(status_lbl)

        content = QVBoxLayout()
        content.setSpacing(2)

        title_style = "font-weight: bold;"
        if deadline.completed:
            title_style += " color: #9ca3af; text-decoration: line-through;"
        title_lbl = QLabel(deadline.title)
        title_lbl.setStyleSheet(title_style)
        content.addWidget(title_lbl)

        date_text = fmt_date_short(deadline.date)
        if deadline.end_date:
            date_text += f" → {fmt_date_short(deadline.end_date)}"
        date_lbl = QLabel(date_text)
        date_lbl.setObjectName("muted")
        date_lbl.setStyleSheet("font-size: 11px;")
        content.addWidget(date_lbl)
        layout.addLayout(content)

        done_btn = QPushButton("✓ Done" if not deadline.completed else "Undo")
        done_btn.setObjectName("icon_btn")
        done_btn.setFixedHeight(24)
        done_btn.clicked.connect(lambda: self.complete_clicked.emit(deadline.id))
        layout.addWidget(done_btn)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("icon_btn")
        del_btn.setFixedSize(24, 24)
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(deadline.id))
        layout.addWidget(del_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_clicked.emit(self.deadline.id)
        super().mousePressEvent(event)


class CalendarView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # Left: calendar
        cal_widget = QWidget()
        cal_layout = QVBoxLayout(cal_widget)
        cal_layout.setContentsMargins(16, 12, 8, 12)
        cal_layout.setSpacing(8)

        cal_header = QHBoxLayout()
        cal_title = QLabel("Calendar")
        cal_title.setObjectName("section_title")
        cal_header.addWidget(cal_title)
        cal_header.addStretch()
        cal_layout.addLayout(cal_header)

        self._calendar = GSDCalendarWidget()
        self._calendar.selectionChanged.connect(self._on_date_selected)
        cal_layout.addWidget(self._calendar)

        # Day detail panel
        self._day_label = QLabel()
        self._day_label.setObjectName("muted")
        cal_layout.addWidget(self._day_label)

        self._day_list = QWidget()
        self._day_list_layout = QVBoxLayout(self._day_list)
        self._day_list_layout.setContentsMargins(0, 0, 0, 0)
        self._day_list_layout.setSpacing(4)
        cal_layout.addWidget(self._day_list)
        cal_layout.addStretch()

        # Right: deadline list
        dl_widget = QWidget()
        dl_layout = QVBoxLayout(dl_widget)
        dl_layout.setContentsMargins(8, 12, 16, 12)
        dl_layout.setSpacing(8)

        dl_header = QHBoxLayout()
        dl_title = QLabel("Deadlines")
        dl_title.setObjectName("section_title")
        dl_header.addWidget(dl_title)
        dl_header.addStretch()
        new_dl_btn = QPushButton("＋ New Deadline")
        new_dl_btn.setObjectName("primary")
        new_dl_btn.clicked.connect(self._new_deadline)
        dl_header.addWidget(new_dl_btn)
        dl_layout.addLayout(dl_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._dl_content = QWidget()
        self._dl_layout = QVBoxLayout(self._dl_content)
        self._dl_layout.setSpacing(6)
        self._dl_layout.setContentsMargins(0, 0, 0, 0)
        self._dl_layout.addStretch()
        scroll.setWidget(self._dl_content)
        dl_layout.addWidget(scroll)

        splitter.addWidget(cal_widget)
        splitter.addWidget(dl_widget)
        splitter.setSizes([500, 400])
        outer.addWidget(splitter)

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def refresh(self) -> None:
        if not self._project_id:
            return

        today = date.today()
        year = self._calendar.yearShown()
        month = self._calendar.monthShown()

        # Get first/last day of displayed month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        start_str = first_day.isoformat()
        end_str = last_day.isoformat()

        # Build event sets
        tasks = task_repo.get_all(self._project_id)
        task_dates = {t.due_date for t in tasks if t.due_date}

        deadlines = deadline_repo.get_all(self._project_id)
        deadline_dates = {d.date for d in deadlines}
        deadline_ranges = [
            (d.date, d.end_date) for d in deadlines if d.end_date
        ]

        notes = note_repo.get_all(self._project_id)
        note_dates = {n.date for n in notes if n.date}

        self._calendar.set_events(task_dates, deadline_dates, note_dates, deadline_ranges)
        self._refresh_deadline_list(deadlines)

    def _refresh_deadline_list(self, deadlines=None) -> None:
        while self._dl_layout.count() > 1:
            child = self._dl_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if deadlines is None:
            deadlines = deadline_repo.get_all(self._project_id)

        if not deadlines:
            empty = QLabel("No deadlines yet.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("padding: 30px;")
            self._dl_layout.insertWidget(0, empty)
            return

        for dl in deadlines:
            row = DeadlineRowWidget(dl)
            row.edit_clicked.connect(self._edit_deadline)
            row.delete_clicked.connect(self._delete_deadline)
            row.complete_clicked.connect(self._toggle_complete)
            self._dl_layout.insertWidget(self._dl_layout.count() - 1, row)

    def _on_date_selected(self) -> None:
        selected = self._calendar.selectedDate()
        date_str = selected.toString("yyyy-MM-dd")
        self._day_label.setText(f"Selected: {selected.toString('MMMM d, yyyy')}")

        # Clear day detail
        while self._day_list_layout.count():
            child = self._day_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._project_id:
            return

        tasks = task_repo.get_for_date(self._project_id, date_str)
        for t in tasks:
            lbl = QLabel(f"  ✅ {t.title}")
            lbl.setStyleSheet("font-size: 12px;")
            self._day_list_layout.addWidget(lbl)

        deadlines = [d for d in deadline_repo.get_all(self._project_id)
                     if d.date == date_str or (d.end_date and d.date <= date_str <= d.end_date)]
        for d in deadlines:
            lbl = QLabel(f"  📅 {d.title}")
            lbl.setStyleSheet("font-size: 12px; color: #ef4444;")
            self._day_list_layout.addWidget(lbl)

    def _new_deadline(self) -> None:
        if not self._project_id:
            return
        try:
            from ..widgets.deadline_dialog import DeadlineDialog
            from ..widgets.toast import show_toast
            from ...utils.search import rebuild_index
            dlg = DeadlineDialog(self._project_id, parent=self.window())
            if dlg.exec():
                dl = dlg.get_deadline()
                deadline_repo.create(self._project_id, dl.title, dl.date, dl.end_date, dl.description)
                rebuild_index(self._project_id)
                self.refresh()
                show_toast(self.window(), "Deadline added!", "success")
        except Exception:
            pass

    def _edit_deadline(self, dl_id: str) -> None:
        dl = deadline_repo.get(dl_id)
        if not dl:
            return
        try:
            from ..widgets.deadline_dialog import DeadlineDialog
            from ..widgets.toast import show_toast
            from ...utils.search import rebuild_index
            dlg = DeadlineDialog(self._project_id, deadline=dl, parent=self.window())
            if dlg.exec():
                if dlg.is_deleted():
                    deadline_repo.delete(dl_id)
                    show_toast(self.window(), "Deadline deleted", "info")
                else:
                    updated = dlg.get_deadline()
                    deadline_repo.update(updated)
                    show_toast(self.window(), "Deadline updated", "success")
                rebuild_index(self._project_id)
                self.refresh()
        except Exception:
            pass

    def _delete_deadline(self, dl_id: str) -> None:
        reply = QMessageBox.question(self, "Delete Deadline", "Delete this deadline?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            deadline_repo.delete(dl_id)
            from ...utils.search import rebuild_index
            rebuild_index(self._project_id)
            self.refresh()

    def _toggle_complete(self, dl_id: str) -> None:
        dl = deadline_repo.get(dl_id)
        if not dl:
            return
        dl.completed = not dl.completed
        deadline_repo.update(dl)
        self.refresh()
