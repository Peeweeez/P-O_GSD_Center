"""
project_card.py — Project overview card for the All Projects view.
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ...models.entities import Project
from ...utils.dates import fmt_date_short


def _stat_box(label: str, value: str | int, color: str = "#6b7280") -> QFrame:
    """Small stat sub-card used in the 2x2 grid."""
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame { background: transparent; border: none; }"
    )
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(4, 4, 4, 4)
    lay.setSpacing(0)

    val_lbl = QLabel(str(value))
    val_font = QFont()
    val_font.setBold(True)
    val_font.setPointSize(16)
    val_lbl.setFont(val_font)
    val_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    lbl_lbl = QLabel(label)
    lbl_lbl.setObjectName("muted")
    lbl_lbl.setStyleSheet("font-size: 10px; background: transparent; border: none;")
    lbl_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    lay.addWidget(val_lbl)
    lay.addWidget(lbl_lbl)
    return frame


class ProjectCard(QFrame):
    """
    Project overview card.

    stats dict keys
    ---------------
    open, critical, overdue, ideas, completion (int 0-100), next_deadline (dict|None)
    next_deadline = {"title": str, "date": str}

    Signals
    -------
    edit_clicked(project_id)
    archive_clicked(project_id)
    select_clicked(project_id)
    """

    edit_clicked = pyqtSignal(str)
    archive_clicked = pyqtSignal(str)
    select_clicked = pyqtSignal(str)

    def __init__(self, project: Project, stats: dict, parent=None):
        super().__init__(parent)
        self._project = project
        self._stats = stats

        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(220)
        self.setMaximumWidth(360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._build_ui()

    # ── build ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        p = self._project
        s = self._stats
        color = p.color or "#3b82f6"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(0)

        # ── color bar ──────────────────────────────────────────────────
        bar = QFrame()
        bar.setFixedHeight(5)
        bar.setStyleSheet(
            f"QFrame {{ background-color: {color}; border-top-left-radius: 8px;"
            f" border-top-right-radius: 8px; border: none; }}"
        )
        root.addWidget(bar)

        # ── header: name + hover buttons ──────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(14, 10, 10, 4)
        header.setSpacing(6)

        name_lbl = QLabel(p.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(13)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet("background: transparent; border: none;")
        header.addWidget(name_lbl, stretch=1)

        self._edit_btn = QPushButton("✎")
        self._edit_btn.setObjectName("icon_btn")
        self._edit_btn.setFixedSize(26, 26)
        self._edit_btn.setToolTip("Edit project")
        self._edit_btn.setVisible(False)
        self._edit_btn.clicked.connect(lambda: self.edit_clicked.emit(p.id))
        header.addWidget(self._edit_btn)

        archive_label = "Unarchive" if p.archived else "Archive"
        self._archive_btn = QPushButton("📦")
        self._archive_btn.setObjectName("icon_btn")
        self._archive_btn.setFixedSize(26, 26)
        self._archive_btn.setToolTip(archive_label)
        self._archive_btn.setVisible(False)
        self._archive_btn.clicked.connect(lambda: self.archive_clicked.emit(p.id))
        header.addWidget(self._archive_btn)

        root.addLayout(header)

        # ── status badge ──────────────────────────────────────────────
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(14, 0, 14, 6)
        status_colors = {
            "active": ("#d1fae5", "#065f46"),
            "on-hold": ("#fef3c7", "#92400e"),
            "complete": ("#dbeafe", "#1e40af"),
        }
        sb_bg, sb_fg = status_colors.get(p.status, ("#f3f4f6", "#374151"))
        status_lbl = QLabel(p.status.upper())
        status_lbl.setStyleSheet(
            f"background-color: {sb_bg}; color: {sb_fg}; border-radius: 3px;"
            f" padding: 1px 8px; font-size: 10px; font-weight: bold; border: none;"
        )
        badge_row.addWidget(status_lbl)
        badge_row.addStretch()
        root.addLayout(badge_row)

        # ── 2x2 stat grid ─────────────────────────────────────────────
        grid = QGridLayout()
        grid.setContentsMargins(14, 0, 14, 8)
        grid.setSpacing(4)
        grid.addWidget(_stat_box("Open", s.get("open", 0), "#3b82f6"), 0, 0)
        grid.addWidget(_stat_box("Critical", s.get("critical", 0), "#ef4444"), 0, 1)
        grid.addWidget(_stat_box("Overdue", s.get("overdue", 0), "#f97316"), 1, 0)
        grid.addWidget(_stat_box("Ideas", s.get("ideas", 0), "#8b5cf6"), 1, 1)
        root.addLayout(grid)

        # ── progress bar ──────────────────────────────────────────────
        prog_row = QHBoxLayout()
        prog_row.setContentsMargins(14, 4, 14, 4)
        prog_row.setSpacing(8)

        pct = s.get("completion", 0)
        prog = QProgressBar()
        prog.setRange(0, 100)
        prog.setValue(pct)
        prog.setTextVisible(False)
        prog.setFixedHeight(6)
        prog_row.addWidget(prog, stretch=1)

        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setObjectName("muted")
        pct_lbl.setStyleSheet("font-size: 11px; background: transparent; border: none;")
        pct_lbl.setFixedWidth(32)
        prog_row.addWidget(pct_lbl)
        root.addLayout(prog_row)

        # ── next deadline ─────────────────────────────────────────────
        nd = s.get("next_deadline")
        if nd:
            dl_text = f"Next: {nd['title']} — {fmt_date_short(nd['date'])}"
        else:
            dl_text = "No upcoming deadlines"
        dl_lbl = QLabel(dl_text)
        dl_lbl.setObjectName("muted")
        dl_lbl.setStyleSheet(
            "font-size: 11px; padding: 0 14px; background: transparent; border: none;"
        )
        dl_lbl.setWordWrap(True)
        root.addWidget(dl_lbl)

    # ── hover ─────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._edit_btn.setVisible(True)
        self._archive_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._edit_btn.setVisible(False)
        self._archive_btn.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            if isinstance(child, QPushButton):
                super().mousePressEvent(event)
                return
            self.select_clicked.emit(self._project.id)
        super().mousePressEvent(event)
