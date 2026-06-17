from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QDateEdit,
    QLabel, QPushButton, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from ...models.entities import Note
from ...utils.uid import uid
from ...utils.dates import now_str, today_str


class NoteDialog(QDialog):
    def __init__(self, project_id: str, note: Note = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._note = note
        self._deleted = False
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Note" if note else "New Note")
        self._build_ui()
        if note:
            self._populate(note)

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
        self._title_edit.setPlaceholderText("Note title…")
        form.addRow("Title:", self._title_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "Meeting Notes", "Decision", "Research", "Draft", "Reference"
        ])
        form.addRow("Type:", self._type_combo)

        # Date row with optional toggle
        date_row = QHBoxLayout()
        self._has_date = QCheckBox("Set date")
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setEnabled(False)
        self._has_date.toggled.connect(self._date_edit.setEnabled)
        date_row.addWidget(self._has_date)
        date_row.addWidget(self._date_edit)
        date_row.addStretch()
        form.addRow("Date:", date_row)

        root.addLayout(form)

        content_lbl = QLabel("Content")
        content_lbl.setObjectName("muted")
        root.addWidget(content_lbl)

        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("Write your note here… (markdown supported)")
        self._content_edit.setMinimumHeight(200)
        root.addWidget(self._content_edit)

        # Buttons
        btn_row = QHBoxLayout()

        if self._note:
            del_btn = QPushButton("Delete Note")
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
    def _populate(self, note: Note):
        self._title_edit.setText(note.title)
        idx = self._type_combo.findText(note.type)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        if note.date:
            self._has_date.setChecked(True)
            self._date_edit.setEnabled(True)
            self._date_edit.setDate(QDate.fromString(note.date, "yyyy-MM-dd"))
        self._content_edit.setPlainText(note.content)

    # ------------------------------------------------------------------
    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Note title is required.")
            return
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    def is_deleted(self) -> bool:
        return self._deleted

    def get_note(self) -> Note:
        title = self._title_edit.text().strip()
        note_type = self._type_combo.currentText()
        date = (
            self._date_edit.date().toString("yyyy-MM-dd")
            if self._has_date.isChecked()
            else None
        )
        content = self._content_edit.toPlainText().strip()

        if self._note:
            n = self._note
            n.title = title
            n.type = note_type
            n.date = date
            n.content = content
            return n
        else:
            return Note(
                id=uid(),
                project_id=self._project_id,
                title=title,
                content=content,
                date=date,
                type=note_type,
                created_at=now_str(),
            )
