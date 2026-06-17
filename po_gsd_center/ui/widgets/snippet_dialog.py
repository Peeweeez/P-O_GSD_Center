from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit,
    QLabel, QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ...models.entities import Snippet
from ...utils.uid import uid
from ...utils.dates import now_str


class SnippetDialog(QDialog):
    def __init__(self, project_id: str, snippet: Snippet = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._snippet = snippet
        self._deleted = False
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowTitle("Edit Snippet" if snippet else "New Snippet")
        self._build_ui()
        if snippet:
            self._populate(snippet)

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

        self._label_edit = QLineEdit()
        self._label_edit.setPlaceholderText("Snippet label…")
        form.addRow("Label:", self._label_edit)

        root.addLayout(form)

        text_lbl = QLabel("Content")
        text_lbl.setObjectName("muted")
        root.addWidget(text_lbl)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Paste or type your snippet here…")
        self._text_edit.setMinimumHeight(220)

        mono_font = QFont("Courier New")
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        mono_font.setPointSize(12)
        self._text_edit.setFont(mono_font)

        root.addWidget(self._text_edit)

        # Buttons
        btn_row = QHBoxLayout()

        if self._snippet:
            del_btn = QPushButton("Delete Snippet")
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
    def _populate(self, snippet: Snippet):
        self._label_edit.setText(snippet.label)
        self._text_edit.setPlainText(snippet.text)

    # ------------------------------------------------------------------
    def _on_save(self):
        if not self._label_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Snippet label is required.")
            return
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Delete Snippet",
            "Are you sure you want to delete this snippet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    def is_deleted(self) -> bool:
        return self._deleted

    def get_snippet(self) -> Snippet:
        label = self._label_edit.text().strip()
        text = self._text_edit.toPlainText()

        if self._snippet:
            s = self._snippet
            s.label = label
            s.text = text
            return s
        else:
            return Snippet(
                id=uid(),
                project_id=self._project_id,
                label=label,
                text=text,
                created_at=now_str(),
            )
