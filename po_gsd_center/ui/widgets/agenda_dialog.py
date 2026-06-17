from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QTextBrowser, QSplitter,
    QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from ...models.entities import Task
from ...db.repositories import task_repo, note_repo
from ...utils.dates import today_str, fmt_date_short


class AgendaDialog(QDialog):
    def __init__(self, project_id: str, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._tasks: list[Task] = []
        self._generated_md: str = ""
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(560)
        self.setWindowTitle("Build Meeting Agenda")
        self._build_ui()
        self._load_tasks()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(24, 20, 24, 20)

        header = QLabel("Build Meeting Agenda")
        header.setObjectName("section_title")
        root.addWidget(header)

        # Meeting title
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Meeting title:"))
        self._meeting_title = QLineEdit()
        self._meeting_title.setPlaceholderText("e.g. Sprint Planning, Team Sync…")
        title_row.addWidget(self._meeting_title)
        root.addLayout(title_row)

        # Splitter: task list | preview
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: tasks
        left_widget_box = QGroupBox("Open Tasks")
        left_layout = QVBoxLayout(left_widget_box)

        hint = QLabel("Select tasks to include in the agenda:")
        hint.setObjectName("muted")
        left_layout.addWidget(hint)

        self._task_list = QListWidget()
        self._task_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._task_list.itemChanged.connect(self._on_item_changed)
        left_layout.addWidget(self._task_list)

        splitter.addWidget(left_widget_box)

        # Right: preview
        right_widget_box = QGroupBox("Preview")
        right_layout = QVBoxLayout(right_widget_box)

        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(False)
        right_layout.addWidget(self._preview)

        splitter.addWidget(right_widget_box)
        splitter.setSizes([280, 380])
        root.addWidget(splitter)

        # Action buttons
        btn_row = QHBoxLayout()

        gen_btn = QPushButton("Generate Note")
        gen_btn.clicked.connect(self._generate)
        btn_row.addWidget(gen_btn)

        save_btn = QPushButton("Save as Note")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save_as_note)
        btn_row.addWidget(save_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _load_tasks(self):
        all_tasks = task_repo.get_all(self._project_id)
        self._tasks = [t for t in all_tasks if t.status != "done"]

        self._task_list.blockSignals(True)
        self._task_list.clear()
        for task in self._tasks:
            label = task.title
            if task.stakeholder:
                label += f"  [{task.stakeholder}]"
            if task.due_date:
                label += f"  — {fmt_date_short(task.due_date)}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            self._task_list.addItem(item)
        self._task_list.blockSignals(False)

    # ------------------------------------------------------------------
    def _on_item_changed(self, item: QListWidgetItem):
        # Auto-refresh preview when selections change, if already generated once
        if self._generated_md:
            self._generate()

    # ------------------------------------------------------------------
    def _selected_tasks(self) -> list[Task]:
        selected_ids = set()
        for i in range(self._task_list.count()):
            item = self._task_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_ids.add(item.data(Qt.ItemDataRole.UserRole))
        return [t for t in self._tasks if t.id in selected_ids]

    # ------------------------------------------------------------------
    def _build_markdown(self, selected: list[Task]) -> str:
        meeting_title = self._meeting_title.text().strip() or "Meeting"
        today = today_str()

        # Collect unique stakeholders
        stakeholders = []
        seen = set()
        for t in selected:
            if t.stakeholder and t.stakeholder not in seen:
                stakeholders.append(t.stakeholder)
                seen.add(t.stakeholder)
        attendees_str = ", ".join(stakeholders) if stakeholders else "_TBD_"

        lines = [
            f"# {meeting_title}",
            f"**Date:** {today}",
            f"**Attendees:** {attendees_str}",
            "",
            "## Agenda",
        ]

        for t in selected:
            due_part = f", due: {fmt_date_short(t.due_date)}" if t.due_date else ""
            stakeholder_part = f"{t.stakeholder}" if t.stakeholder else ""
            meta = ", ".join(p for p in [stakeholder_part] if p)
            if due_part:
                meta = (meta + due_part) if meta else due_part.lstrip(", ")
            header_part = f" ({meta})" if meta else ""
            lines.append(f"- {t.title}{header_part}")
            if t.description:
                snippet = t.description[:100].replace("\n", " ")
                if len(t.description) > 100:
                    snippet += "…"
                lines.append(f"  {snippet}")

        lines += [
            "",
            "## Action Items",
            "- [ ] ",
            "",
            "## Decisions",
            "- ",
            "",
            "## Notes",
            "",
        ]

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _generate(self):
        selected = self._selected_tasks()
        if not selected:
            QMessageBox.information(
                self, "No Tasks Selected",
                "Please check at least one task to include in the agenda.",
            )
            return

        self._generated_md = self._build_markdown(selected)
        self._preview.setMarkdown(self._generated_md)

    # ------------------------------------------------------------------
    def _save_as_note(self):
        selected = self._selected_tasks()
        if not selected:
            QMessageBox.information(
                self, "No Tasks Selected",
                "Please check at least one task and generate the agenda first.",
            )
            return

        md = self._generated_md or self._build_markdown(selected)
        meeting_title = self._meeting_title.text().strip() or "Meeting"

        note_repo.create(
            project_id=self._project_id,
            title=meeting_title,
            content=md,
            date=today_str(),
            type="Meeting Notes",
        )

        QMessageBox.information(
            self, "Saved",
            f'Meeting note "{meeting_title}" has been saved to this project\'s Notes.',
        )
        self.accept()
