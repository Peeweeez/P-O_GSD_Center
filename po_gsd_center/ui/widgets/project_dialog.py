from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QLabel, QPushButton, QDialogButtonBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from ...models.entities import Project
from ...utils.uid import uid
from ...utils.dates import now_str
from .color_picker import ColorPicker


class ProjectDialog(QDialog):
    def __init__(self, project: Project = None, parent=None):
        super().__init__(parent)
        self._project = project
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Project" if project else "New Project")
        self._build_ui()
        if project:
            self._populate(project)

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title label
        title_lbl = QLabel(self.windowTitle())
        title_lbl.setObjectName("section_title")
        layout.addWidget(title_lbl)

        # Form
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Project name…")
        form.addRow("Name:", self._name_edit)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["active", "on-hold", "complete"])
        form.addRow("Status:", self._status_combo)

        self._color_picker = ColorPicker()
        form.addRow("Color:", self._color_picker)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _populate(self, project: Project):
        self._name_edit.setText(project.name)
        idx = self._status_combo.findText(project.status)
        if idx >= 0:
            self._status_combo.setCurrentIndex(idx)
        self._color_picker.set_selected(project.color)

    # ------------------------------------------------------------------
    def _on_save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Project name is required.")
            return
        self.accept()

    # ------------------------------------------------------------------
    def get_data(self) -> dict:
        return {
            "name": self._name_edit.text().strip(),
            "color": self._color_picker.selected(),
            "status": self._status_combo.currentText(),
        }
