from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QDateEdit,
    QLabel, QPushButton, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from ...models.entities import Deadline
from ...utils.uid import uid
from ...utils.dates import now_str


class DeadlineDialog(QDialog):
    def __init__(self, project_id: str, deadline: Deadline = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._deadline = deadline
        self._deleted = False
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Deadline" if deadline else "New Deadline")
        self._build_ui()
        if deadline:
            self._populate(deadline)

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
        self._title_edit.setPlaceholderText("Deadline title…")
        form.addRow("Title:", self._title_edit)

        # Start date (required)
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self._date_edit)

        # End date (optional)
        end_row = QHBoxLayout()
        self._has_end = QCheckBox("Set end date")
        self._end_date_edit = QDateEdit()
        self._end_date_edit.setCalendarPopup(True)
        self._end_date_edit.setDate(QDate.currentDate())
        self._end_date_edit.setEnabled(False)
        self._has_end.toggled.connect(self._end_date_edit.setEnabled)
        end_row.addWidget(self._has_end)
        end_row.addWidget(self._end_date_edit)
        end_row.addStretch()
        form.addRow("End Date:", end_row)

        self._completed_check = QCheckBox("Completed")
        form.addRow("", self._completed_check)

        root.addLayout(form)

        desc_lbl = QLabel("Description")
        desc_lbl.setObjectName("muted")
        root.addWidget(desc_lbl)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Optional description…")
        self._desc_edit.setFixedHeight(100)
        root.addWidget(self._desc_edit)

        # Buttons
        btn_row = QHBoxLayout()

        if self._deadline:
            del_btn = QPushButton("Delete Deadline")
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
    def _populate(self, deadline: Deadline):
        self._title_edit.setText(deadline.title)
        if deadline.date:
            self._date_edit.setDate(QDate.fromString(deadline.date, "yyyy-MM-dd"))
        if deadline.end_date:
            self._has_end.setChecked(True)
            self._end_date_edit.setEnabled(True)
            self._end_date_edit.setDate(QDate.fromString(deadline.end_date, "yyyy-MM-dd"))
        self._completed_check.setChecked(deadline.completed)
        self._desc_edit.setPlainText(deadline.description)

    # ------------------------------------------------------------------
    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Deadline title is required.")
            return
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Delete Deadline",
            "Are you sure you want to delete this deadline?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    def is_deleted(self) -> bool:
        return self._deleted

    def get_deadline(self) -> Deadline:
        title = self._title_edit.text().strip()
        date = self._date_edit.date().toString("yyyy-MM-dd")
        end_date = (
            self._end_date_edit.date().toString("yyyy-MM-dd")
            if self._has_end.isChecked()
            else None
        )
        completed = self._completed_check.isChecked()
        description = self._desc_edit.toPlainText().strip()

        if self._deadline:
            d = self._deadline
            d.title = title
            d.date = date
            d.end_date = end_date
            d.completed = completed
            d.description = description
            return d
        else:
            return Deadline(
                id=uid(),
                project_id=self._project_id,
                title=title,
                date=date,
                end_date=end_date,
                description=description,
                completed=completed,
                created_at=now_str(),
            )
