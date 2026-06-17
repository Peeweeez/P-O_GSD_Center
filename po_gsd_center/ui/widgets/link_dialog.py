from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit,
    QLabel, QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt

from ...models.entities import Link
from ...utils.uid import uid
from ...utils.dates import now_str


class LinkDialog(QDialog):
    def __init__(self, project_id: str, link: Link = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._link = link
        self._deleted = False
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Link" if link else "New Link")
        self._build_ui()
        if link:
            self._populate(link)

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

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://…")
        form.addRow("URL *:", self._url_edit)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Display title (optional)")
        form.addRow("Title:", self._title_edit)

        self._category_edit = QLineEdit()
        self._category_edit.setPlaceholderText("e.g. Documentation, Reference…")
        form.addRow("Category:", self._category_edit)

        root.addLayout(form)

        desc_lbl = QLabel("Description")
        desc_lbl.setObjectName("muted")
        root.addWidget(desc_lbl)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Optional description…")
        self._desc_edit.setFixedHeight(80)
        root.addWidget(self._desc_edit)

        # Buttons
        btn_row = QHBoxLayout()

        if self._link:
            del_btn = QPushButton("Delete Link")
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
    def _populate(self, link: Link):
        self._url_edit.setText(link.url)
        self._title_edit.setText(link.title)
        self._category_edit.setText(link.category)
        self._desc_edit.setPlainText(link.description)

    # ------------------------------------------------------------------
    def _on_save(self):
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Validation", "URL is required.")
            return
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Delete Link",
            "Are you sure you want to delete this link?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._deleted = True
            self.accept()

    # ------------------------------------------------------------------
    def is_deleted(self) -> bool:
        return self._deleted

    def get_link(self) -> Link:
        url = self._url_edit.text().strip()
        title = self._title_edit.text().strip()
        category = self._category_edit.text().strip()
        description = self._desc_edit.toPlainText().strip()

        if self._link:
            lk = self._link
            lk.url = url
            lk.title = title
            lk.category = category
            lk.description = description
            return lk
        else:
            return Link(
                id=uid(),
                project_id=self._project_id,
                url=url,
                title=title,
                category=category,
                description=description,
                created_at=now_str(),
            )
