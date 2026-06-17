"""
overview_view.py — Dashboard / overview for a single project.
"""
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QProgressBar, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from ...db.repositories import task_repo, deadline_repo, note_repo, idea_repo, link_repo
from ...db.repositories import project_repo
from ...utils.dates import (
    countdown_label, fmt_date_short, is_overdue, week_dates, today_str,
)
from ..widgets.kpi_card import KpiCard


# ── helpers ────────────────────────────────────────────────────────────────

def _section_header(title: str, nav_label: str = "", callback=None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setContentsMargins(0, 4, 0, 4)
    lbl = QLabel(title)
    lbl.setObjectName("section_title")
    row.addWidget(lbl)
    row.addStretch()
    if nav_label and callback:
        btn = QPushButton(nav_label)
        btn.setObjectName("icon_btn")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(callback)
        row.addWidget(btn)
    return row


def _card_frame() -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    return f


def _muted(text: str, wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("muted")
    lbl.setStyleSheet("background: transparent; border: none;")
    if wrap:
        lbl.setWordWrap(True)
    return lbl


# ── quadrant box ────────────────────────────────────────────────────────────

QUADRANT_META = {
    "do":       ("Do",       "#fee2e2", "#b91c1c"),
    "schedule": ("Schedule", "#fef3c7", "#92400e"),
    "delegate": ("Delegate", "#dbeafe", "#1e40af"),
    "eliminate":("Eliminate","#f3f4f6", "#374151"),
}


class _QuadrantBox(QFrame):
    clicked_signal = pyqtSignal()

    def __init__(self, quadrant: str, count: int, top_task: str = "", parent=None):
        super().__init__(parent)
        label, bg, fg = QUADRANT_META.get(quadrant, (quadrant, "#f3f4f6", "#374151"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: 6px; border: none; }}"
        )
        self.setMinimumHeight(72)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)

        name_lbl = QLabel(label)
        name_font = QFont()
        name_font.setBold(True)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet(
            f"color: {fg}; background: transparent; border: none; font-size: 12px;"
        )
        lay.addWidget(name_lbl)

        cnt_lbl = QLabel(str(count))
        cnt_font = QFont()
        cnt_font.setBold(True)
        cnt_font.setPointSize(18)
        cnt_lbl.setFont(cnt_font)
        cnt_lbl.setStyleSheet(
            f"color: {fg}; background: transparent; border: none;"
        )
        lay.addWidget(cnt_lbl)

        if top_task:
            t_lbl = QLabel(top_task)
            t_lbl.setStyleSheet(
                f"color: {fg}; background: transparent; border: none;"
                f" font-size: 11px; opacity: 0.8;"
            )
            t_lbl.setWordWrap(True)
            lay.addWidget(t_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_signal.emit()
        super().mousePressEvent(event)


# ── main view ───────────────────────────────────────────────────────────────

class OverviewView(QScrollArea):
    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: str = ""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setObjectName("overview_container")
        self._root = QVBoxLayout(self._container)
        self._root.setContentsMargins(24, 20, 24, 24)
        self._root.setSpacing(16)
        self.setWidget(self._container)

        # KPI cards row
        self._kpi_row = QHBoxLayout()
        self._kpi_row.setSpacing(12)
        self._kpi_open = KpiCard("Open Tasks", "–", accent="#3b82f6")
        self._kpi_over = KpiCard("Overdue", "–", accent="#ef4444")
        self._kpi_dl   = KpiCard("Deadlines", "–", accent="#f97316")
        self._kpi_pct  = KpiCard("Completion", "–%", accent="#22c55e")
        for kpi in (self._kpi_open, self._kpi_over, self._kpi_dl, self._kpi_pct):
            self._kpi_row.addWidget(kpi)
        self._root.addLayout(self._kpi_row)

        # Progress bar
        prog_frame = _card_frame()
        prog_layout = QVBoxLayout(prog_frame)
        prog_layout.setContentsMargins(16, 12, 16, 12)
        prog_layout.setSpacing(6)
        prog_header = QHBoxLayout()
        self._prog_lbl = QLabel("Overall Progress")
        self._prog_lbl.setObjectName("section_title")
        self._prog_pct_lbl = _muted("0%")
        prog_header.addWidget(self._prog_lbl)
        prog_header.addStretch()
        prog_header.addWidget(self._prog_pct_lbl)
        prog_layout.addLayout(prog_header)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(10)
        prog_layout.addWidget(self._progress_bar)
        self._root.addWidget(prog_frame)

        # Middle two-column row (tasks + deadlines)
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # Left: open tasks
        self._tasks_frame = _card_frame()
        self._tasks_layout = QVBoxLayout(self._tasks_frame)
        self._tasks_layout.setContentsMargins(14, 12, 14, 12)
        self._tasks_layout.setSpacing(4)
        mid_row.addWidget(self._tasks_frame, stretch=2)

        # Right: upcoming deadlines
        self._dl_frame = _card_frame()
        self._dl_layout = QVBoxLayout(self._dl_frame)
        self._dl_layout.setContentsMargins(14, 12, 14, 12)
        self._dl_layout.setSpacing(4)
        mid_row.addWidget(self._dl_frame, stretch=1)

        self._root.addLayout(mid_row)

        # This Week strip
        self._week_frame = _card_frame()
        self._week_outer = QVBoxLayout(self._week_frame)
        self._week_outer.setContentsMargins(14, 12, 14, 12)
        self._week_outer.setSpacing(8)
        self._root.addWidget(self._week_frame)

        # Priority Matrix
        self._matrix_frame = _card_frame()
        self._matrix_outer = QVBoxLayout(self._matrix_frame)
        self._matrix_outer.setContentsMargins(14, 12, 14, 12)
        self._matrix_outer.setSpacing(8)
        self._root.addWidget(self._matrix_frame)

        # Bottom three-column row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        self._notes_frame = _card_frame()
        self._notes_layout = QVBoxLayout(self._notes_frame)
        self._notes_layout.setContentsMargins(14, 12, 14, 12)
        self._notes_layout.setSpacing(4)

        self._ideas_frame = _card_frame()
        self._ideas_layout = QVBoxLayout(self._ideas_frame)
        self._ideas_layout.setContentsMargins(14, 12, 14, 12)
        self._ideas_layout.setSpacing(4)

        self._links_frame = _card_frame()
        self._links_layout = QVBoxLayout(self._links_frame)
        self._links_layout.setContentsMargins(14, 12, 14, 12)
        self._links_layout.setSpacing(4)

        for f in (self._notes_frame, self._ideas_frame, self._links_frame):
            bottom_row.addWidget(f, stretch=1)
        self._root.addLayout(bottom_row)

        self._root.addStretch()

    # ── public API ────────────────────────────────────────────────────────

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def refresh(self) -> None:
        if not self._project_id:
            return
        pid = self._project_id
        stats = project_repo.get_stats(pid)

        # KPI
        self._kpi_open.set_value(str(stats["open"]))
        self._kpi_over.set_value(str(stats["overdue"]))
        upcoming_count = len(deadline_repo.get_upcoming(pid, limit=99))
        self._kpi_dl.set_value(str(upcoming_count))
        pct = stats["completion"]
        self._kpi_pct.set_value(f"{pct}%")

        # Progress bar
        self._progress_bar.setValue(pct)
        self._prog_pct_lbl.setText(f"{pct}%")

        self._refresh_tasks(pid)
        self._refresh_deadlines(pid)
        self._refresh_week(pid)
        self._refresh_matrix(pid)
        self._refresh_recent_notes(pid)
        self._refresh_recent_ideas(pid)
        self._refresh_recent_links(pid)

    # ── sub-refresh helpers ───────────────────────────────────────────────

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _refresh_tasks(self, pid: str) -> None:
        lay = self._tasks_layout
        self._clear_layout(lay)

        lay.addLayout(
            _section_header("Open Tasks", "View all →",
                            lambda: self.navigate_to.emit("tasks"))
        )

        tasks = [t for t in task_repo.get_all(pid, sort="smart") if t.status != "done"][:6]
        if not tasks:
            lay.addWidget(_muted("No open tasks. Nice work!"))
        else:
            for task in tasks:
                row = QHBoxLayout()
                row.setSpacing(8)
                dot = QLabel("●")
                pri_colors = {
                    "critical": "#ef4444", "high": "#f59e0b",
                    "medium": "#3b82f6", "low": "#9ca3af",
                }
                dot.setStyleSheet(
                    f"color: {pri_colors.get(task.priority, '#9ca3af')};"
                    f" background: transparent; border: none; font-size: 10px;"
                )
                dot.setFixedWidth(14)
                row.addWidget(dot)

                t_lbl = QLabel(task.title)
                t_lbl.setStyleSheet("background: transparent; border: none;")
                t_lbl.setWordWrap(True)
                row.addWidget(t_lbl, stretch=1)

                if task.due_date:
                    overdue = is_overdue(task.due_date)
                    due_lbl = _muted(countdown_label(task.due_date))
                    if overdue:
                        due_lbl.setStyleSheet(
                            "color: #ef4444; background: transparent; border: none;"
                        )
                    row.addWidget(due_lbl)

                lay.addLayout(row)
        lay.addStretch()

    def _refresh_deadlines(self, pid: str) -> None:
        lay = self._dl_layout
        self._clear_layout(lay)

        lay.addLayout(
            _section_header("Upcoming Deadlines", "View all →",
                            lambda: self.navigate_to.emit("calendar"))
        )

        deadlines = deadline_repo.get_upcoming(pid, limit=5)
        if not deadlines:
            lay.addWidget(_muted("No upcoming deadlines."))
        else:
            for dl in deadlines:
                dl_lbl = QLabel(f"• {dl.title}")
                dl_lbl.setStyleSheet("background: transparent; border: none;")
                dl_lbl.setWordWrap(True)
                lay.addWidget(dl_lbl)

                date_str = fmt_date_short(dl.date)
                if dl.end_date:
                    date_str += f" → {fmt_date_short(dl.end_date)}"
                lay.addWidget(_muted(date_str))

        lay.addStretch()

    def _refresh_week(self, pid: str) -> None:
        outer = self._week_outer
        self._clear_layout(outer)

        outer.addLayout(
            _section_header("This Week")
        )

        today = today_str()
        days = week_dates()

        strip = QHBoxLayout()
        strip.setSpacing(6)

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d in enumerate(days):
            d_str = d.isoformat()
            tasks_that_day = task_repo.get_for_date(pid, d_str)
            count = len(tasks_that_day)
            is_today = d_str == today

            cell = QFrame()
            cell.setStyleSheet(
                "QFrame { background-color: %s; border-radius: 6px; border: %s; }"
                % (
                    "#3b82f6" if is_today else "rgba(0,0,0,0.04)",
                    "2px solid #3b82f6" if is_today else "1px solid transparent",
                )
            )
            cell.setFixedWidth(56)
            cell.setMinimumHeight(64)

            cell_lay = QVBoxLayout(cell)
            cell_lay.setContentsMargins(4, 6, 4, 6)
            cell_lay.setSpacing(2)
            cell_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            day_lbl = QLabel(day_names[i % 7])
            day_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_lbl.setStyleSheet(
                "font-size: 11px; background: transparent; border: none;"
                + (" color: white; font-weight: bold;" if is_today else " color: #6b7280;")
            )
            cell_lay.addWidget(day_lbl)

            num_lbl = QLabel(str(d.day))
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_font = QFont()
            num_font.setBold(True)
            num_lbl.setFont(num_font)
            num_lbl.setStyleSheet(
                "background: transparent; border: none;"
                + (" color: white;" if is_today else "")
            )
            cell_lay.addWidget(num_lbl)

            count_lbl = QLabel(str(count) if count else "")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_lbl.setStyleSheet(
                "font-size: 11px; background: transparent; border: none;"
                + (" color: rgba(255,255,255,0.8);" if is_today else " color: #9ca3af;")
            )
            cell_lay.addWidget(count_lbl)

            strip.addWidget(cell)

        strip.addStretch()
        outer.addLayout(strip)

    def _refresh_matrix(self, pid: str) -> None:
        outer = self._matrix_outer
        self._clear_layout(outer)

        outer.addLayout(
            _section_header("Priority Matrix", "Go to Tasks →",
                            lambda: self.navigate_to.emit("tasks"))
        )

        grid = QGridLayout()
        grid.setSpacing(10)

        positions = [
            ("do",        0, 0),
            ("schedule",  0, 1),
            ("delegate",  1, 0),
            ("eliminate", 1, 1),
        ]
        for quad, row, col in positions:
            tasks_q = task_repo.get_for_quadrant(pid, quad)
            count = len(tasks_q)
            top = tasks_q[0].title if tasks_q else ""
            box = _QuadrantBox(quad, count, top_task=top[:40] + ("…" if len(top) > 40 else ""))
            box.clicked_signal.connect(lambda: self.navigate_to.emit("tasks"))
            grid.addWidget(box, row, col)

        outer.addLayout(grid)

    def _refresh_recent_notes(self, pid: str) -> None:
        lay = self._notes_layout
        self._clear_layout(lay)
        lay.addLayout(
            _section_header("Notes", "View all →",
                            lambda: self.navigate_to.emit("notes"))
        )
        notes = note_repo.get_all(pid)[:2]
        if not notes:
            lay.addWidget(_muted("No notes yet."))
        else:
            for n in notes:
                title_lbl = QLabel(n.title or "(untitled)")
                title_font = QFont()
                title_font.setBold(True)
                title_lbl.setFont(title_font)
                title_lbl.setStyleSheet("background: transparent; border: none;")
                lay.addWidget(title_lbl)
                preview = (n.content or "")[:80].replace("\n", " ")
                lay.addWidget(_muted(preview + ("…" if len(n.content or "") > 80 else ""), wrap=True))
        lay.addStretch()

    def _refresh_recent_ideas(self, pid: str) -> None:
        lay = self._ideas_layout
        self._clear_layout(lay)
        lay.addLayout(
            _section_header("Ideas", "View all →",
                            lambda: self.navigate_to.emit("ideas"))
        )
        ideas = idea_repo.get_all(pid, show_archived=False)[:2]
        if not ideas:
            lay.addWidget(_muted("No ideas yet."))
        else:
            for idea in ideas:
                title_lbl = QLabel(idea.title or "(untitled)")
                title_font = QFont()
                title_font.setBold(True)
                title_lbl.setFont(title_font)
                title_lbl.setStyleSheet("background: transparent; border: none;")
                lay.addWidget(title_lbl)
                tags_str = "  ".join(f"#{t}" for t in (idea.tags or [])[:3])
                if tags_str:
                    lay.addWidget(_muted(tags_str))
        lay.addStretch()

    def _refresh_recent_links(self, pid: str) -> None:
        lay = self._links_layout
        self._clear_layout(lay)
        lay.addLayout(
            _section_header("Links", "View all →",
                            lambda: self.navigate_to.emit("links"))
        )
        links = link_repo.get_all(pid)[:2]
        if not links:
            lay.addWidget(_muted("No links yet."))
        else:
            for lnk in links:
                display = lnk.title or lnk.url
                title_lbl = QLabel(display)
                title_font = QFont()
                title_font.setBold(True)
                title_lbl.setFont(title_font)
                title_lbl.setStyleSheet("background: transparent; border: none;")
                title_lbl.setWordWrap(True)
                lay.addWidget(title_lbl)
                if lnk.category:
                    lay.addWidget(_muted(lnk.category))
        lay.addStretch()
