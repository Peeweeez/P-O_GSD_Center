"""
ideas_view.py — Ideas bank view for a single project.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QTextEdit, QDateEdit, QMessageBox, QCheckBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ...db.repositories import idea_repo, task_repo
from ...models.entities import Idea, Task
from ...utils.uid import uid
from ...utils.dates import now_str, fmt_date_short
from ...utils.search import rebuild_index
from ..widgets.toast import show_toast


# ── Idea dialog ───────────────────────────────────────────────────────────────

class _IdeaDialog(QDialog):
    def __init__(self, project_id: str, idea: Idea = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._idea = idea
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowTitle("Edit Idea" if idea else "New Idea")
        self._build_ui()
        if idea:
            self._populate(idea)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        hdr = QLabel(self.windowTitle())
        hdr.setObjectName("section_title")
        root.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Idea title…")
        form.addRow("Title:", self._title_edit)

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("Comma-separated tags, e.g. ux, research")
        form.addRow("Tags:", self._tags_edit)

        self._due_check = QCheckBox("Set due date")
        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDate(QDate.currentDate())
        self._due_edit.setEnabled(False)
        self._due_check.toggled.connect(self._due_edit.setEnabled)
        due_row = QHBoxLayout()
        due_row.addWidget(self._due_check)
        due_row.addWidget(self._due_edit)
        due_row.addStretch()
        form.addRow("Due Date:", due_row)

        root.addLayout(form)

        body_lbl = QLabel("Body")
        body_lbl.setObjectName("muted")
        root.addWidget(body_lbl)

        self._body_edit = QTextEdit()
        self._body_edit.setPlaceholderText("Describe the idea…")
        self._body_edit.setMinimumHeight(180)
        root.addWidget(self._body_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    def _populate(self, idea: Idea):
        self._title_edit.setText(idea.title or "")
        self._tags_edit.setText(", ".join(idea.tags or []))
        if idea.due_date:
            self._due_check.setChecked(True)
            self._due_edit.setDate(QDate.fromString(idea.due_date, "yyyy-MM-dd"))
        self._body_edit.setPlainText(idea.body or "")

    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Title is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        raw_tags = self._tags_edit.text()
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        due = (
            self._due_edit.date().toString("yyyy-MM-dd")
            if self._due_check.isChecked()
            else None
        )
        return {
            "title": self._title_edit.text().strip(),
            "tags": tags,
            "due_date": due,
            "body": self._body_edit.toPlainText().strip(),
        }


# ── row builder ───────────────────────────────────────────────────────────────

def _make_idea_row(
    idea: Idea,
    on_archive,
    on_convert,
    on_edit,
    on_delete,
) -> QFrame:
    row = QFrame()
    row.setObjectName("card")
    row.setMinimumHeight(56)

    if idea.archived:
        row.setStyleSheet(
            "QFrame#card { opacity: 0.6; background-color: rgba(0,0,0,0.03); "
            "border-radius: 6px; border: 1px solid transparent; }"
        )

    lay = QHBoxLayout(row)
    lay.setContentsMargins(12, 8, 8, 8)
    lay.setSpacing(10)

    text_col = QVBoxLayout()
    text_col.setSpacing(3)
    text_col.setContentsMargins(0, 0, 0, 0)

    title_lbl = QLabel(idea.title or "(untitled)")
    title_font = QFont()
    title_font.setBold(True)
    if idea.archived:
        title_font.setStrikeOut(True)
    title_lbl.setFont(title_font)
    title_lbl.setStyleSheet(
        "background: transparent; border: none;"
        + (" color: #9ca3af;" if idea.archived else "")
    )
    text_col.addWidget(title_lbl)

    meta_row = QHBoxLayout()
    meta_row.setSpacing(6)
    meta_row.setContentsMargins(0, 0, 0, 0)

    # Tags as mini badges
    for tag in (idea.tags or [])[:3]:
        badge = QLabel(f"#{tag}")
        badge.setStyleSheet(
            "background-color: #dbeafe; color: #1e40af; border-radius: 3px;"
            " padding: 1px 6px; font-size: 11px; border: none;"
        )
        badge.setFixedHeight(18)
        meta_row.addWidget(badge)

    if len(idea.tags or []) > 3:
        more = QLabel(f"+{len(idea.tags) - 3}")
        more.setObjectName("muted")
        more.setStyleSheet("font-size: 11px; background: transparent; border: none;")
        meta_row.addWidget(more)

    if idea.due_date:
        due_lbl = QLabel(fmt_date_short(idea.due_date))
        due_lbl.setObjectName("muted")
        due_lbl.setStyleSheet("font-size: 11px; background: transparent; border: none;")
        meta_row.addWidget(due_lbl)

    meta_row.addStretch()
    text_col.addLayout(meta_row)

    if idea.body:
        preview = idea.body[:80].replace("\n", " ")
        if len(idea.body) > 80:
            preview += "…"
        body_lbl = QLabel(preview)
        body_lbl.setObjectName("muted")
        body_lbl.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        body_lbl.setWordWrap(True)
        text_col.addWidget(body_lbl)

    lay.addLayout(text_col, stretch=1)

    archive_label = "Unarchive" if idea.archived else "Archive"
    arch_btn = QPushButton(archive_label)
    arch_btn.setFixedHeight(28)
    arch_btn.clicked.connect(on_archive)
    lay.addWidget(arch_btn)

    if not idea.archived:
        convert_btn = QPushButton("→ Task")
        convert_btn.setFixedHeight(28)
        convert_btn.setToolTip("Convert to Task")
        convert_btn.clicked.connect(on_convert)
        lay.addWidget(convert_btn)

    edit_btn = QPushButton("Edit")
    edit_btn.setFixedHeight(28)
    edit_btn.clicked.connect(on_edit)
    lay.addWidget(edit_btn)

    del_btn = QPushButton("Delete")
    del_btn.setObjectName("danger")
    del_btn.setFixedHeight(28)
    del_btn.clicked.connect(on_delete)
    lay.addWidget(del_btn)

    return row


# ── main view ─────────────────────────────────────────────────────────────────

class IdeasView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: str = ""
        self._show_archived = False
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_lbl = QLabel("Ideas")
        title_lbl.setObjectName("section_title")
        header.addWidget(title_lbl)
        header.addStretch()

        self._archive_toggle = QPushButton("Show Archived")
        self._archive_toggle.setCheckable(True)
        self._archive_toggle.toggled.connect(self._on_archive_toggle)
        header.addWidget(self._archive_toggle)

        new_btn = QPushButton("+ New Idea")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._on_new_idea)
        header.addWidget(new_btn)
        root.addLayout(header)

        # Scroll list
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        root.addWidget(self._scroll)

    # ── public API ────────────────────────────────────────────────────────

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def refresh(self) -> None:
        if not self._project_id:
            return
        self._populate_list()

    # ── internal ─────────────────────────────────────────────────────────

    def _on_archive_toggle(self, checked: bool):
        self._show_archived = checked
        self._archive_toggle.setText("Hide Archived" if checked else "Show Archived")
        self._populate_list()

    def _clear_list(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_list(self):
        self._clear_list()
        ideas = idea_repo.get_all(self._project_id, show_archived=self._show_archived)

        if not ideas:
            empty = QLabel("No ideas yet. Capture your first idea!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("muted")
            self._list_layout.insertWidget(0, empty)
            return

        for idea in ideas:
            row = _make_idea_row(
                idea,
                on_archive=lambda _=idea: self._on_archive_idea(_),
                on_convert=lambda _=idea: self._on_convert_to_task(_),
                on_edit=lambda _=idea: self._on_edit_idea(_),
                on_delete=lambda _=idea: self._on_delete_idea(_),
            )
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _on_new_idea(self):
        dlg = _IdeaDialog(self._project_id, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            idea_repo.create(
                self._project_id,
                title=data["title"],
                body=data["body"],
                tags=data["tags"],
                due_date=data["due_date"],
            )
            rebuild_index(self._project_id)
            self._populate_list()
            show_toast(self.window(), "Idea saved", "success")

    def _on_edit_idea(self, idea: Idea):
        dlg = _IdeaDialog(self._project_id, idea=idea, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            idea.title = data["title"]
            idea.body = data["body"]
            idea.tags = data["tags"]
            idea.due_date = data["due_date"]
            idea_repo.update(idea)
            rebuild_index(self._project_id)
            self._populate_list()
            show_toast(self.window(), "Idea updated", "success")

    def _on_archive_idea(self, idea: Idea):
        idea.archived = not idea.archived
        idea_repo.update(idea)
        self._populate_list()
        label = "archived" if idea.archived else "unarchived"
        show_toast(self.window(), f"Idea {label}", "info")

    def _on_delete_idea(self, idea: Idea):
        reply = QMessageBox.question(
            self, "Delete Idea", "Delete this idea permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            idea_repo.delete(idea.id)
            rebuild_index(self._project_id)
            self._populate_list()
            show_toast(self.window(), "Idea deleted", "info")

    def _on_convert_to_task(self, idea: Idea):
        task_repo.create(
            self._project_id,
            title=idea.title,
            description=idea.body or "",
            priority="medium",
            status="todo",
        )
        idea_repo.delete(idea.id)
        rebuild_index(self._project_id)
        self._populate_list()
        show_toast(self.window(), "Idea converted to task", "success")
