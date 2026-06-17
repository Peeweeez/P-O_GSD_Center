from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QDateEdit,
    QLabel, QPushButton, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from ...models.entities import Idea
from ...utils.uid import uid
from ...utils.dates import now_str


class IdeaDialog(QDialog):
    def __init__(self, project_id: str, idea: Idea = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._idea = idea
        self._deleted = False
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Idea" if idea else "New Idea")
        self._build_ui()
        if idea:
            self._populate(idea)

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(24, 20, 24, 20)

        header = QLabel(self.windowTitle())
        header.setObjectName("section_title")
        root.addWidget(header)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Idea title…")
        form.addRow("Title:", self._title_edit)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("tag1, tag2, tag3")
        form.addRow("Tags:", self._tags_edit)

        # Due date (optional)
        due_row = QHBoxLayout()
        self._has_due = QCheckBox("Set due date")
        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDate(QDate.currentDate())
        self._due_edit.setEnabled(False)
        self._has_due.toggled.connect(self._due_edit.setEnabled)
        due_row.addWidget(self._has_due)
        due_row.addWidget(self._due_edit)
        due_row.addStretch()
        form.addRow("Due Date:", due_row)

        self._archived_check = QCheckBox("Archived")
        form.addRow("", self._archived_check)

        root.addLayout(form)

        body_lbl = QLabel("Body")
        body_lbl.setObjectName("muted")
        root.addWidget(body_lbl)

        self._body_edit = QTextEdit()
        self._body_edit.setPlaceholderText("Describe your idea… (markdown supported)")
        self._body_edit.setMinimumHeight(160)
        root.addWidget(self._body_edit)

        # Buttons
        btn_row = QHBoxLayout()

        if self._idea:
            del_btn = QPushButton("Delete Idea")
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
    def _populate(self, idea: Idea):
        self._title_edit.setText(idea.title)
        self._tags_edit.setText(", ".join(idea.tags))
        if idea.due_date:
            self._has_due.setChecked(True)
            self._due_edit.setEnabled(True)
            self._due_edit.setDate(QDate.fromString(idea.due_date, "yyyy-MM-dd"))
        self._archived_check.setChecked(idea.archived)
        self._body_edit.setPlainText(idea.body)

    # ------------------------------------------------------------------
    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Idea title is required.")
            return
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Delete Idea",
            "Are you sure you want to delete this idea?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    def is_deleted(self) -> bool:
        return self._deleted

    def get_idea(self) -> Idea:
        title = self._title_edit.text().strip()
        raw_tags = self._tags_edit.text().strip()
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()] if raw_tags else []
        due_date = (
            self._due_edit.date().toString("yyyy-MM-dd")
            if self._has_due.isChecked()
            else None
        )
        archived = self._archived_check.isChecked()
        body = self._body_edit.toPlainText().strip()

        if self._idea:
            i = self._idea
            i.title = title
            i.body = body
            i.tags = tags
            i.due_date = due_date
            i.archived = archived
            return i
        else:
            return Idea(
                id=uid(),
                project_id=self._project_id,
                title=title,
                body=body,
                tags=tags,
                due_date=due_date,
                archived=archived,
                created_at=now_str(),
            )
