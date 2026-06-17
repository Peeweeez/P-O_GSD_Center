"""
notes_view.py — Notes view for a single project.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDateEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from ...db.repositories import note_repo
from ...models.entities import Note
from ...utils.uid import uid
from ...utils.dates import now_str, today_str, fmt_date_short
from ...utils.search import rebuild_index
from ..widgets.entry_row import EntryRow
from ..widgets.toast import show_toast
from ..widgets.markdown_editor import MarkdownEditor


# ── Note dialog ─────────────────────────────────────────────────────────────

class _NoteDialog(QDialog):
    def __init__(self, project_id: str, note: Note = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._note = note
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setWindowTitle("Edit Note" if note else "New Note")
        self._build_ui()
        if note:
            self._populate(note)

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
        self._title_edit.setPlaceholderText("Note title…")
        form.addRow("Title:", self._title_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["", "meeting", "idea", "reference", "action", "other"])
        form.addRow("Type:", self._type_combo)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self._date_edit)

        root.addLayout(form)

        content_lbl = QLabel("Content")
        content_lbl.setObjectName("muted")
        root.addWidget(content_lbl)

        self._editor = MarkdownEditor()
        self._editor.setMinimumHeight(260)
        root.addWidget(self._editor)

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

    def _populate(self, note: Note):
        self._title_edit.setText(note.title or "")
        idx = self._type_combo.findText(note.type or "")
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        if note.date:
            self._date_edit.setDate(QDate.fromString(note.date, "yyyy-MM-dd"))
        self._editor.set_content(note.content or "")

    def _on_save(self):
        self.accept()

    def get_data(self) -> dict:
        return {
            "title": self._title_edit.text().strip(),
            "type": self._type_combo.currentText(),
            "date": self._date_edit.date().toString("yyyy-MM-dd"),
            "content": self._editor.get_content(),
        }


# ── main view ───────────────────────────────────────────────────────────────

class NotesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: str = ""
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_lbl = QLabel("Notes")
        title_lbl.setObjectName("section_title")
        header.addWidget(title_lbl)
        header.addStretch()
        new_btn = QPushButton("+ New Note")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._on_new_note)
        header.addWidget(new_btn)
        root.addLayout(header)

        # Scroll area for note rows
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

    def _clear_list(self):
        while self._list_layout.count() > 1:  # keep the trailing stretch
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_list(self):
        self._clear_list()
        notes = note_repo.get_all(self._project_id)

        if not notes:
            empty = QLabel("No notes yet. Create your first note.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("muted")
            self._list_layout.insertWidget(0, empty)
            return

        for note in notes:
            type_str = f"[{note.type}]  " if note.type else ""
            date_str = fmt_date_short(note.date) if note.date else ""
            subtitle = f"{type_str}{date_str}"
            preview = (note.content or "").replace("\n", " ")[:80]
            if len(note.content or "") > 80:
                preview += "…"
            if preview:
                subtitle = (subtitle + "  —  " + preview) if subtitle else preview

            row = EntryRow(
                title=note.title or "(untitled)",
                subtitle=subtitle,
                icon="📝",
                actions=[
                    ("Edit", lambda _=note: self._on_edit_note(_)),
                    ("Delete", lambda _=note: self._on_delete_note(_)),
                ],
                item_id=note.id,
            )
            row.edit_clicked.connect(self._on_edit_note_by_id)
            row.delete_clicked.connect(self._on_delete_note_by_id)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _on_new_note(self):
        dlg = _NoteDialog(self._project_id, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            note_repo.create(
                self._project_id,
                title=data["title"],
                content=data["content"],
                date=data["date"],
                type=data["type"],
            )
            rebuild_index(self._project_id)
            self.refresh()
            show_toast(self.window(), "Note created", "success")

    def _on_edit_note_by_id(self, note_id: str):
        note = note_repo.get(note_id)
        if note:
            self._on_edit_note(note)

    def _on_edit_note(self, note: Note):
        dlg = _NoteDialog(self._project_id, note=note, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            note.title = data["title"]
            note.content = data["content"]
            note.date = data["date"]
            note.type = data["type"]
            note_repo.update(note)
            rebuild_index(self._project_id)
            self.refresh()
            show_toast(self.window(), "Note updated", "success")

    def _on_delete_note_by_id(self, note_id: str):
        reply = QMessageBox.question(
            self, "Delete Note", "Delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            note_repo.delete(note_id)
            rebuild_index(self._project_id)
            self.refresh()
            show_toast(self.window(), "Note deleted", "info")

    def _on_delete_note(self, note: Note):
        self._on_delete_note_by_id(note.id)
