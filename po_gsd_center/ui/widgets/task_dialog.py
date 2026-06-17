from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QDateEdit,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ...models.entities import Task, Subtask, Comment
from ...utils.uid import uid
from ...utils.dates import now_str, today_str


class TaskDialog(QDialog):
    def __init__(self, project_id: str, task: Task = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._task = task
        self._deleted = False
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowTitle("Edit Task" if task else "New Task")
        self._subtasks: list[Subtask] = list(task.subtasks) if task else []
        self._comments: list[Comment] = list(task.comments) if task else []
        self._build_ui()
        if task:
            self._populate(task)

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(24, 20, 24, 20)

        # Header title
        header = QLabel(self.windowTitle())
        header.setObjectName("section_title")
        root.addWidget(header)

        # --- Title field (large, bold) ---
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Task title…")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._title_edit.setFont(title_font)
        root.addWidget(self._title_edit)

        # --- Description ---
        desc_lbl = QLabel("Description")
        desc_lbl.setObjectName("muted")
        root.addWidget(desc_lbl)
        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Add description… (markdown supported)")
        self._desc_edit.setFixedHeight(100)
        root.addWidget(self._desc_edit)

        # --- Form fields ---
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["critical", "high", "medium", "low"])
        self._priority_combo.setCurrentText("medium")
        form.addRow("Priority:", self._priority_combo)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["todo", "in-progress", "blocked", "review", "done"])
        form.addRow("Status:", self._status_combo)

        # Due date row
        due_row = QHBoxLayout()
        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDate(QDate.currentDate())
        self._due_edit.setSpecialValueText("None")
        self._due_edit.setMinimumDate(QDate(2000, 1, 1))
        self._has_due = QCheckBox("Set due date")
        self._has_due.toggled.connect(self._due_edit.setEnabled)
        self._due_edit.setEnabled(False)
        due_row.addWidget(self._has_due)
        due_row.addWidget(self._due_edit)
        due_row.addStretch()
        form.addRow("Due Date:", due_row)

        self._stakeholder_edit = QLineEdit()
        self._stakeholder_edit.setPlaceholderText("e.g. Alice")
        form.addRow("Stakeholder:", self._stakeholder_edit)

        self._recurrence_combo = QComboBox()
        self._recurrence_combo.addItems(["none", "daily", "weekly", "biweekly", "monthly"])
        form.addRow("Recurrence:", self._recurrence_combo)

        self._quadrant_combo = QComboBox()
        self._quadrant_combo.addItems(["none", "do", "schedule", "delegate", "eliminate"])
        form.addRow("Quadrant:", self._quadrant_combo)

        self._pinned_check = QCheckBox("Pinned")
        form.addRow("", self._pinned_check)

        root.addLayout(form)

        # --- Subtasks ---
        subtask_group = QGroupBox("Subtasks")
        st_layout = QVBoxLayout(subtask_group)
        st_layout.setSpacing(6)

        self._subtask_list = QListWidget()
        self._subtask_list.setFixedHeight(110)
        self._subtask_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._subtask_list.customContextMenuRequested.connect(self._remove_subtask_ctx)
        st_layout.addWidget(self._subtask_list)

        add_st_row = QHBoxLayout()
        self._subtask_input = QLineEdit()
        self._subtask_input.setPlaceholderText("New subtask…")
        self._subtask_input.returnPressed.connect(self._add_subtask)
        add_st_btn = QPushButton("Add")
        add_st_btn.clicked.connect(self._add_subtask)
        add_st_row.addWidget(self._subtask_input)
        add_st_row.addWidget(add_st_btn)
        st_layout.addLayout(add_st_row)

        root.addWidget(subtask_group)

        # --- Comments ---
        comment_group = QGroupBox("Comments")
        cm_layout = QVBoxLayout(comment_group)
        cm_layout.setSpacing(6)

        self._comment_list = QListWidget()
        self._comment_list.setFixedHeight(90)
        cm_layout.addWidget(self._comment_list)

        add_cm_row = QHBoxLayout()
        self._comment_input = QLineEdit()
        self._comment_input.setPlaceholderText("Add comment…")
        self._comment_input.returnPressed.connect(self._add_comment)
        add_cm_btn = QPushButton("Add")
        add_cm_btn.clicked.connect(self._add_comment)
        add_cm_row.addWidget(self._comment_input)
        add_cm_row.addWidget(add_cm_btn)
        cm_layout.addLayout(add_cm_row)

        root.addWidget(comment_group)

        # --- Bottom buttons ---
        btn_row = QHBoxLayout()

        if self._task:
            del_btn = QPushButton("Delete Task")
            del_btn.setObjectName("danger")
            del_btn.clicked.connect(self._on_delete)
            btn_row.addWidget(del_btn)

        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _populate(self, task: Task):
        self._title_edit.setText(task.title)
        self._desc_edit.setPlainText(task.description)
        self._priority_combo.setCurrentText(task.priority)
        self._status_combo.setCurrentText(task.status)

        if task.due_date:
            self._has_due.setChecked(True)
            self._due_edit.setEnabled(True)
            self._due_edit.setDate(QDate.fromString(task.due_date, "yyyy-MM-dd"))
        else:
            self._has_due.setChecked(False)
            self._due_edit.setEnabled(False)

        self._stakeholder_edit.setText(task.stakeholder)
        self._recurrence_combo.setCurrentText(task.recurrence)
        self._quadrant_combo.setCurrentText(task.quadrant)
        self._pinned_check.setChecked(task.pinned)

        for st in self._subtasks:
            self._append_subtask_item(st)

        for cm in self._comments:
            self._append_comment_item(cm)

    # ------------------------------------------------------------------
    # Subtask helpers
    def _append_subtask_item(self, st: Subtask):
        item = QListWidgetItem(st.title)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if st.done else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, st.id)
        self._subtask_list.addItem(item)

    def _add_subtask(self):
        text = self._subtask_input.text().strip()
        if not text:
            return
        st = Subtask(id=uid(), title=text, done=False)
        self._subtasks.append(st)
        self._append_subtask_item(st)
        self._subtask_input.clear()

    def _remove_subtask_ctx(self, pos):
        item = self._subtask_list.itemAt(pos)
        if not item:
            return
        st_id = item.data(Qt.ItemDataRole.UserRole)
        self._subtasks = [s for s in self._subtasks if s.id != st_id]
        row = self._subtask_list.row(item)
        self._subtask_list.takeItem(row)

    # ------------------------------------------------------------------
    # Comment helpers
    def _append_comment_item(self, cm: Comment):
        short_at = cm.at[:16].replace("T", " ")
        item = QListWidgetItem(f"{short_at} — {cm.text}")
        item.setData(Qt.ItemDataRole.UserRole, cm.id)
        self._comment_list.addItem(item)

    def _add_comment(self):
        text = self._comment_input.text().strip()
        if not text:
            return
        cm = Comment(id=uid(), text=text, at=now_str())
        self._comments.append(cm)
        self._append_comment_item(cm)
        self._comment_input.clear()

    # ------------------------------------------------------------------
    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Task title is required.")
            return
        # Sync subtask done states from list widget
        for i in range(self._subtask_list.count()):
            item = self._subtask_list.item(i)
            st_id = item.data(Qt.ItemDataRole.UserRole)
            done = item.checkState() == Qt.CheckState.Checked
            for st in self._subtasks:
                if st.id == st_id:
                    st.done = done
                    break
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Delete Task",
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    def is_deleted(self) -> bool:
        return self._deleted

    def get_task(self) -> Task:
        title = self._title_edit.text().strip()
        description = self._desc_edit.toPlainText().strip()
        priority = self._priority_combo.currentText()
        status = self._status_combo.currentText()
        due_date = (
            self._due_edit.date().toString("yyyy-MM-dd")
            if self._has_due.isChecked()
            else None
        )
        stakeholder = self._stakeholder_edit.text().strip()
        recurrence = self._recurrence_combo.currentText()
        quadrant = self._quadrant_combo.currentText()
        pinned = self._pinned_check.isChecked()

        if self._task:
            t = self._task
            t.title = title
            t.description = description
            t.priority = priority
            t.status = status
            t.due_date = due_date
            t.stakeholder = stakeholder
            t.recurrence = recurrence
            t.quadrant = quadrant
            t.pinned = pinned
            t.subtasks = self._subtasks
            t.comments = self._comments
            if status == "done" and not t.completed_at:
                t.completed_at = now_str()
            elif status != "done":
                t.completed_at = None
            return t
        else:
            return Task(
                id=uid(),
                project_id=self._project_id,
                title=title,
                description=description,
                priority=priority,
                status=status,
                due_date=due_date,
                stakeholder=stakeholder,
                recurrence=recurrence,
                quadrant=quadrant,
                pinned=pinned,
                subtasks=self._subtasks,
                comments=self._comments,
                created_at=now_str(),
                completed_at=now_str() if status == "done" else None,
            )
