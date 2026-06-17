"""
task_row.py — Task row widget for the task list view.
"""
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...models.entities import Task
from ...utils.dates import countdown_label, is_overdue
from ..style import PRIORITY_COLORS, PRIORITY_COLORS_DARK, STATUS_COLORS, STATUS_COLORS_DARK


def _badge(text: str, bg: str, fg: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background-color: {bg}; color: {fg}; border-radius: 3px;"
        f" padding: 1px 6px; font-size: 11px; border: none;"
    )
    lbl.setFixedHeight(18)
    return lbl


class TaskRow(QFrame):
    """
    A styled card row representing a single task.

    Signals
    -------
    status_toggled(task_id)
    priority_changed(task_id, new_priority)
    delete_clicked(task_id)
    edit_clicked(task_id)
    selected_changed(task_id, bool)
    """

    status_toggled = pyqtSignal(str)
    priority_changed = pyqtSignal(str, str)
    delete_clicked = pyqtSignal(str)
    edit_clicked = pyqtSignal(str)
    selected_changed = pyqtSignal(str, bool)

    def __init__(self, task: Task, dark_mode: bool = False, parent=None):
        super().__init__(parent)
        self._task = task
        self._dark = dark_mode
        self._hovered = False

        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()
        self._apply_style(hovered=False)

    # ── build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        task = self._task
        pc = PRIORITY_COLORS_DARK if self._dark else PRIORITY_COLORS
        sc = STATUS_COLORS_DARK if self._dark else STATUS_COLORS
        p_bg, p_fg, p_dot = pc.get(task.priority, pc["medium"])
        s_bg, s_fg = sc.get(task.status, sc["todo"])

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(8)

        # Bulk-select checkbox
        self._select_cb = QCheckBox()
        self._select_cb.setFixedSize(18, 18)
        self._select_cb.stateChanged.connect(
            lambda state: self.selected_changed.emit(
                task.id, state == Qt.CheckState.Checked.value
            )
        )
        outer.addWidget(self._select_cb)

        # Priority dot
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            f"background-color: {p_dot}; border-radius: 5px; border: none;"
        )
        outer.addWidget(dot)

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        text_col.setContentsMargins(0, 0, 0, 0)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        title_row.setContentsMargins(0, 0, 0, 0)

        done = task.status == "done"
        self._title_lbl = QLabel(task.title)
        title_font = QFont()
        title_font.setBold(True)
        if done:
            title_font.setStrikeOut(True)
        self._title_lbl.setFont(title_font)
        self._title_lbl.setStyleSheet(
            f"background: transparent; border: none;"
            + (" color: #9ca3af;" if done else "")
        )
        title_row.addWidget(self._title_lbl)

        if task.pinned:
            pin_lbl = QLabel("📌")
            pin_lbl.setStyleSheet("background: transparent; border: none; font-size: 12px;")
            title_row.addWidget(pin_lbl)

        title_row.addStretch()
        text_col.addLayout(title_row)

        # Meta row: priority badge, status badge, due date, stakeholder, subtask count
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)
        meta_row.setContentsMargins(0, 0, 0, 0)

        meta_row.addWidget(_badge(task.priority.upper(), p_bg, p_fg))
        meta_row.addWidget(_badge(task.status.replace("-", " ").upper(), s_bg, s_fg))

        if task.due_date:
            overdue = is_overdue(task.due_date) and not done
            cd = countdown_label(task.due_date)
            due_lbl = QLabel(cd)
            due_lbl.setStyleSheet(
                "background: transparent; border: none; font-size: 11px;"
                + (" color: #ef4444;" if overdue else " color: #6b7280;")
            )
            meta_row.addWidget(due_lbl)

        if task.stakeholder:
            st_lbl = QLabel(f"@{task.stakeholder}")
            st_lbl.setStyleSheet(
                "background: transparent; border: none; font-size: 11px; color: #6b7280;"
            )
            meta_row.addWidget(st_lbl)

        if task.subtasks:
            done_sub = sum(1 for s in task.subtasks if s.done)
            sub_lbl = QLabel(f"{done_sub}/{len(task.subtasks)} subtasks")
            sub_lbl.setStyleSheet(
                "background: transparent; border: none; font-size: 11px; color: #6b7280;"
            )
            meta_row.addWidget(sub_lbl)

        meta_row.addStretch()
        text_col.addLayout(meta_row)

        outer.addLayout(text_col, stretch=1)

        # Hover-only action buttons
        self._pin_btn = QPushButton("📌" if not task.pinned else "📍")
        self._pin_btn.setObjectName("icon_btn")
        self._pin_btn.setToolTip("Toggle pin")
        self._pin_btn.setFixedSize(28, 28)
        self._pin_btn.setVisible(False)
        self._pin_btn.clicked.connect(lambda: self.status_toggled.emit(task.id))
        outer.addWidget(self._pin_btn)

        self._del_btn = QPushButton("🗑")
        self._del_btn.setObjectName("icon_btn")
        self._del_btn.setToolTip("Delete")
        self._del_btn.setFixedSize(28, 28)
        self._del_btn.setVisible(False)
        self._del_btn.clicked.connect(lambda: self.delete_clicked.emit(task.id))
        outer.addWidget(self._del_btn)

    # ── hover ─────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(hovered=True)
        self._pin_btn.setVisible(True)
        self._del_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(hovered=False)
        self._pin_btn.setVisible(False)
        self._del_btn.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Don't fire edit when clicking checkbox or buttons
            child = self.childAt(event.pos())
            if child and (
                isinstance(child, (QCheckBox, QPushButton))
                or (child.parent() and isinstance(child.parent(), QCheckBox))
            ):
                super().mousePressEvent(event)
                return
            self.edit_clicked.emit(self._task.id)
        super().mousePressEvent(event)

    # ── style ─────────────────────────────────────────────────────────────

    def _apply_style(self, hovered: bool) -> None:
        done = self._task.status == "done"
        if hovered:
            bg = "rgba(0,0,0,0.05)"
            border = "rgba(0,0,0,0.12)"
        elif done:
            bg = "rgba(0,0,0,0.02)"
            border = "transparent"
        else:
            bg = "transparent"
            border = "transparent"

        self.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {bg};
                border-radius: 6px;
                border: 1px solid {border};
            }}
            """
        )

    # ── public ────────────────────────────────────────────────────────────

    @property
    def task(self) -> Task:
        return self._task
