from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton,
    QLabel, QLineEdit, QComboBox, QFrame, QScrollArea, QCheckBox,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..widgets.matrix_view import MatrixView
from ..widgets.weekly_view import WeeklyView
from ...db.repositories import task_repo
from ...models.entities import Task
from ...utils.dates import countdown_label, is_overdue, today_str
from ...utils.search import rebuild_index
from ...utils.uid import uid
from ...utils.dates import now_str


TASK_TEMPLATES = [
    ("Meeting Follow-up", "medium", "Review meeting notes and send follow-up actions."),
    ("Change Request",    "high",   "Document and track change request through approval process."),
    ("BRD",               "high",   "Draft Business Requirements Document for stakeholder review."),
    ("UAT",               "medium", "Coordinate User Acceptance Testing with business stakeholders."),
    ("Stakeholder Review","medium", "Prepare material for stakeholder review and gather feedback."),
    ("Regulatory",        "critical","Ensure compliance with regulatory requirements and deadlines."),
]

PRIORITY_DOTS = {
    "critical": "#ef4444",
    "high":     "#f59e0b",
    "medium":   "#3b82f6",
    "low":      "#9ca3af",
}

STATUS_LABELS = {
    "todo":        "To Do",
    "in-progress": "In Progress",
    "blocked":     "Blocked",
    "review":      "Review",
    "done":        "Done",
}


class TaskRowWidget(QFrame):
    status_toggled  = pyqtSignal(str)
    edit_clicked    = pyqtSignal(str)
    delete_clicked  = pyqtSignal(str)
    selected_changed = pyqtSignal(str, bool)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setObjectName("card")
        self.setFixedHeight(62)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # Bulk-select checkbox
        self._check = QCheckBox()
        self._check.stateChanged.connect(lambda s: self.selected_changed.emit(task.id, bool(s)))
        layout.addWidget(self._check)

        # Priority dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {PRIORITY_DOTS.get(task.priority, '#9ca3af')}; font-size: 14px;")
        dot.setFixedWidth(16)
        layout.addWidget(dot)

        # Main content
        content = QVBoxLayout()
        content.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        self._title_lbl = QLabel(task.title)
        if task.pinned:
            self._title_lbl.setText("📌 " + task.title)
        font_style = "font-weight: bold;"
        if task.status == "done":
            font_style += " text-decoration: line-through; color: #9ca3af;"
        self._title_lbl.setStyleSheet(font_style)
        title_row.addWidget(self._title_lbl)
        title_row.addStretch()

        # Status toggle button
        done_btn = QPushButton("✓" if task.status == "done" else "○")
        done_btn.setObjectName("icon_btn")
        done_btn.setFixedSize(24, 24)
        done_btn.setToolTip("Toggle done")
        done_btn.clicked.connect(lambda: self.status_toggled.emit(task.id))
        title_row.addWidget(done_btn)
        content.addLayout(title_row)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        # Priority badge
        prio_badge = QLabel(task.priority.upper())
        prio_colors = {"critical": "#fee2e2:#b91c1c", "high": "#fef3c7:#92400e",
                       "medium": "#dbeafe:#1e40af", "low": "#f3f4f6:#374151"}
        bc = prio_colors.get(task.priority, "#f3f4f6:#374151").split(":")
        prio_badge.setStyleSheet(f"background:{bc[0]};color:{bc[1]};border-radius:3px;padding:0 4px;font-size:10px;")
        meta_row.addWidget(prio_badge)

        # Status badge
        status_lbl = QLabel(STATUS_LABELS.get(task.status, task.status))
        status_lbl.setObjectName("muted")
        status_lbl.setStyleSheet("font-size: 11px;")
        meta_row.addWidget(status_lbl)

        # Due date
        if task.due_date:
            cl = countdown_label(task.due_date)
            due_lbl = QLabel(cl)
            color = "#ef4444" if is_overdue(task.due_date) and task.status != "done" else "#6b7280"
            due_lbl.setStyleSheet(f"font-size: 11px; color: {color};")
            meta_row.addWidget(due_lbl)

        # Stakeholder
        if task.stakeholder:
            sh_lbl = QLabel(f"👤 {task.stakeholder}")
            sh_lbl.setObjectName("muted")
            sh_lbl.setStyleSheet("font-size: 11px;")
            meta_row.addWidget(sh_lbl)

        # Subtask count
        if task.subtasks:
            done_st = sum(1 for s in task.subtasks if s.done)
            st_lbl = QLabel(f"☑ {done_st}/{len(task.subtasks)}")
            st_lbl.setObjectName("muted")
            st_lbl.setStyleSheet("font-size: 11px;")
            meta_row.addWidget(st_lbl)

        meta_row.addStretch()

        # Delete button
        del_btn = QPushButton("🗑")
        del_btn.setObjectName("icon_btn")
        del_btn.setFixedSize(24, 24)
        del_btn.setToolTip("Delete")
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(task.id))
        meta_row.addWidget(del_btn)

        content.addLayout(meta_row)
        layout.addLayout(content)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_clicked.emit(self.task.id)
        super().mousePressEvent(event)

    def is_selected(self) -> bool:
        return self._check.isChecked()


class TaskListSubView(QWidget):
    task_edit_requested = pyqtSignal(str)
    task_new_requested  = pyqtSignal(dict)  # prefill dict
    refresh_needed      = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id = ""
        self._rows: list[TaskRowWidget] = []
        self._selected_ids: set[str] = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Filter bar
        filter_bar = QWidget()
        filter_bar.setFixedHeight(44)
        fl = QHBoxLayout(filter_bar)
        fl.setContentsMargins(8, 4, 8, 4)
        fl.setSpacing(8)

        self._status_filter = QComboBox()
        self._status_filter.addItems(["All Status", "todo", "in-progress", "blocked", "review", "done"])
        self._status_filter.currentIndexChanged.connect(self._refresh_list)
        fl.addWidget(self._status_filter)

        self._prio_filter = QComboBox()
        self._prio_filter.addItems(["All Priority", "critical", "high", "medium", "low"])
        self._prio_filter.currentIndexChanged.connect(self._refresh_list)
        fl.addWidget(self._prio_filter)

        self._sh_filter = QLineEdit()
        self._sh_filter.setPlaceholderText("Filter stakeholder…")
        self._sh_filter.setFixedWidth(160)
        self._sh_filter.textChanged.connect(self._refresh_list)
        fl.addWidget(self._sh_filter)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["Smart", "Priority", "Due Date", "Alphabetical", "Created"])
        self._sort_combo.currentIndexChanged.connect(self._refresh_list)
        fl.addWidget(self._sort_combo)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("icon_btn")
        clear_btn.clicked.connect(self._clear_filters)
        fl.addWidget(clear_btn)
        fl.addStretch()

        # Agenda button
        agenda_btn = QPushButton("📋 Agenda")
        agenda_btn.setObjectName("icon_btn")
        agenda_btn.clicked.connect(self._open_agenda)
        fl.addWidget(agenda_btn)

        outer.addWidget(filter_bar)

        # Bulk action bar (hidden by default)
        self._bulk_bar = QWidget()
        self._bulk_bar.setFixedHeight(36)
        self._bulk_bar.hide()
        bl = QHBoxLayout(self._bulk_bar)
        bl.setContentsMargins(8, 2, 8, 2)
        bl.setSpacing(8)
        self._sel_label = QLabel("0 selected")
        self._sel_label.setObjectName("muted")
        bl.addWidget(self._sel_label)
        done_all_btn = QPushButton("✓ Mark Done")
        done_all_btn.setObjectName("icon_btn")
        done_all_btn.clicked.connect(self._bulk_mark_done)
        bl.addWidget(done_all_btn)
        del_all_btn = QPushButton("🗑 Delete")
        del_all_btn.setObjectName("danger")
        del_all_btn.clicked.connect(self._bulk_delete)
        bl.addWidget(del_all_btn)
        desel_btn = QPushButton("✕ Deselect")
        desel_btn.setObjectName("icon_btn")
        desel_btn.clicked.connect(self._deselect_all)
        bl.addWidget(desel_btn)
        bl.addStretch()
        outer.addWidget(self._bulk_bar)

        # Template chips
        tmpl_bar = QWidget()
        tmpl_bar.setFixedHeight(38)
        tl = QHBoxLayout(tmpl_bar)
        tl.setContentsMargins(8, 4, 8, 4)
        tl.setSpacing(6)
        tmpl_lbl = QLabel("Templates:")
        tmpl_lbl.setObjectName("muted")
        tl.addWidget(tmpl_lbl)
        for name, prio, desc in TASK_TEMPLATES:
            btn = QPushButton(name)
            btn.setFixedHeight(26)
            btn.setStyleSheet("font-size: 11px; padding: 0 8px; border-radius: 12px;")
            btn.clicked.connect(lambda _, n=name, p=prio, d=desc: self.task_new_requested.emit(
                {"title": n, "priority": p, "description": d}
            ))
            tl.addWidget(btn)
        tl.addStretch()
        outer.addWidget(tmpl_bar)

        # Quick-add bar
        qa_bar = QWidget()
        qa_bar.setFixedHeight(44)
        ql = QHBoxLayout(qa_bar)
        ql.setContentsMargins(8, 4, 8, 4)
        ql.setSpacing(8)
        self._quick_input = QLineEdit()
        self._quick_input.setPlaceholderText("Quick add task (press Enter)…")
        self._quick_input.returnPressed.connect(self._quick_add)
        ql.addWidget(self._quick_input)
        add_btn = QPushButton("＋ Add")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(72)
        add_btn.clicked.connect(self._quick_add)
        ql.addWidget(add_btn)
        outer.addWidget(qa_bar)

        # Scrollable task list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_content = QWidget()
        self._list_layout = QVBoxLayout(self._list_content)
        self._list_layout.setContentsMargins(8, 4, 8, 8)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_content)
        outer.addWidget(scroll)

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def _get_sort(self) -> str:
        sorts = ["smart", "priority", "dueDate", "alpha", "created"]
        return sorts[self._sort_combo.currentIndex()]

    def _refresh_list(self) -> None:
        self.refresh()

    def _clear_filters(self) -> None:
        self._status_filter.setCurrentIndex(0)
        self._prio_filter.setCurrentIndex(0)
        self._sh_filter.clear()
        self._sort_combo.setCurrentIndex(0)

    def refresh(self) -> None:
        # Clear layout
        while self._list_layout.count() > 1:
            child = self._list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._rows.clear()
        self._selected_ids.clear()
        self._update_bulk_bar()

        if not self._project_id:
            return

        status_f = self._status_filter.currentText()
        prio_f = self._prio_filter.currentText()
        sh_f = self._sh_filter.text()

        tasks = task_repo.get_all(
            self._project_id,
            status_filter=None if status_f.startswith("All") else status_f,
            priority_filter=None if prio_f.startswith("All") else prio_f,
            stakeholder_filter=sh_f if sh_f else None,
            sort=self._get_sort(),
        )

        pinned = [t for t in tasks if t.pinned and t.status != "done"]
        open_tasks = [t for t in tasks if not t.pinned and t.status != "done"]
        done_tasks = [t for t in tasks if t.status == "done"]

        insert_pos = 0
        if pinned:
            self._add_section("📌 Pinned", pinned, insert_pos)
            insert_pos += 1 + len(pinned)
        if open_tasks:
            self._add_section("Open", open_tasks, insert_pos)
            insert_pos += 1 + len(open_tasks)
        if done_tasks:
            self._add_section("✓ Completed", done_tasks, insert_pos)

        if not tasks:
            empty = QLabel("No tasks match your filters." if (
                status_f != "All Status" or prio_f != "All Priority" or sh_f
            ) else "No tasks yet. Use quick-add or templates above.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("padding: 40px;")
            self._list_layout.insertWidget(0, empty)

    def _add_section(self, title: str, tasks: list[Task], pos: int) -> None:
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #6b7280; padding: 4px 0;")
        self._list_layout.insertWidget(pos, lbl)
        for i, task in enumerate(tasks):
            row = TaskRowWidget(task)
            row.edit_clicked.connect(self.task_edit_requested)
            row.status_toggled.connect(self._on_status_toggled)
            row.delete_clicked.connect(self._on_delete)
            row.selected_changed.connect(self._on_selection_changed)
            self._list_layout.insertWidget(pos + 1 + i, row)
            self._rows.append(row)

    def _on_status_toggled(self, task_id: str) -> None:
        task = task_repo.get(task_id)
        if not task:
            return
        if task.status == "done":
            task.status = "todo"
            task.completed_at = None
            task_repo.update(task)
        else:
            task_repo.mark_done(task)
        rebuild_index(self._project_id)
        self.refresh()
        self.refresh_needed.emit()

    def _on_delete(self, task_id: str) -> None:
        reply = QMessageBox.question(self, "Delete Task", "Delete this task?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            task_repo.delete(task_id)
            rebuild_index(self._project_id)
            self.refresh()
            self.refresh_needed.emit()

    def _on_selection_changed(self, task_id: str, selected: bool) -> None:
        if selected:
            self._selected_ids.add(task_id)
        else:
            self._selected_ids.discard(task_id)
        self._update_bulk_bar()

    def _update_bulk_bar(self) -> None:
        if self._selected_ids:
            self._bulk_bar.show()
            self._sel_label.setText(f"{len(self._selected_ids)} selected")
        else:
            self._bulk_bar.hide()

    def _deselect_all(self) -> None:
        for row in self._rows:
            row._check.setChecked(False)
        self._selected_ids.clear()
        self._update_bulk_bar()

    def _bulk_mark_done(self) -> None:
        ids = list(self._selected_ids)
        task_repo.bulk_set_status(ids, "done")
        rebuild_index(self._project_id)
        self._selected_ids.clear()
        self.refresh()
        self.refresh_needed.emit()

    def _bulk_delete(self) -> None:
        ids = list(self._selected_ids)
        reply = QMessageBox.question(self, "Delete Tasks", f"Delete {len(ids)} task(s)?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            task_repo.bulk_delete(ids)
            rebuild_index(self._project_id)
            self._selected_ids.clear()
            self.refresh()
            self.refresh_needed.emit()

    def _quick_add(self) -> None:
        title = self._quick_input.text().strip()
        if not title or not self._project_id:
            return
        task_repo.create(self._project_id, title)
        rebuild_index(self._project_id)
        self._quick_input.clear()
        self.refresh()
        self.refresh_needed.emit()

    def _open_agenda(self) -> None:
        if not self._project_id:
            return
        try:
            from ..widgets.agenda_dialog import AgendaDialog
            from ..widgets.toast import show_toast
            dlg = AgendaDialog(self._project_id, parent=self.window())
            if dlg.exec():
                rebuild_index(self._project_id)
                show_toast(self.window(), "Meeting note saved!", "success")
                self.refresh_needed.emit()
        except ImportError:
            pass


class TasksView(QWidget):
    refresh_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._list_view = TaskListSubView()
        self._matrix_view = MatrixView()
        self._weekly_view = WeeklyView()

        self._tabs.addTab(self._list_view, "List")
        self._tabs.addTab(self._matrix_view, "Matrix")
        self._tabs.addTab(self._weekly_view, "Weekly")

        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

        # Connect signals
        self._list_view.task_edit_requested.connect(self._open_task_edit)
        self._list_view.task_new_requested.connect(self._open_task_new_prefill)
        self._list_view.refresh_needed.connect(self.refresh_needed)
        self._matrix_view.task_edit_requested.connect(self._open_task_edit)
        self._weekly_view.task_edit_requested.connect(self._open_task_edit)

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id
        self._list_view.set_project_id(project_id)
        self._matrix_view.set_project_id(project_id)
        self._weekly_view.set_project_id(project_id)

    def refresh(self) -> None:
        current = self._tabs.currentIndex()
        if current == 0:
            self._list_view.refresh()
        elif current == 1:
            self._matrix_view.refresh()
        elif current == 2:
            self._weekly_view.refresh()

    def show_list(self) -> None:
        self._tabs.setCurrentIndex(0)

    def show_matrix(self) -> None:
        self._tabs.setCurrentIndex(1)

    def _on_tab_changed(self, idx: int) -> None:
        self.refresh()

    def _open_task_edit(self, task_id: str) -> None:
        task = task_repo.get(task_id)
        if not task:
            return
        try:
            from ..widgets.task_dialog import TaskDialog
            from ..widgets.toast import show_toast
            dlg = TaskDialog(self._project_id, task=task, parent=self.window())
            if dlg.exec():
                updated = dlg.get_task()
                task_repo.update(updated)
                rebuild_index(self._project_id)
                show_toast(self.window(), "Task updated", "success")
                self.refresh()
                self.refresh_needed.emit()
        except ImportError as e:
            pass

    def _open_task_new(self) -> None:
        self._open_task_new_prefill({})

    def _open_task_new_prefill(self, prefill: dict) -> None:
        if not self._project_id:
            return
        try:
            from ..widgets.task_dialog import TaskDialog
            from ..widgets.toast import show_toast
            dlg = TaskDialog(self._project_id, prefill=prefill, parent=self.window())
            if dlg.exec():
                t = dlg.get_task()
                task_repo._insert(t)
                rebuild_index(self._project_id)
                show_toast(self.window(), "Task created", "success")
                self.refresh()
                self.refresh_needed.emit()
        except ImportError:
            pass
