from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QTextBrowser
from PyQt6.QtCore import pyqtSignal
from ...utils.markdown import render_md


class MarkdownEditor(QWidget):
    content_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._preview_mode = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        self._toggle_btn = QPushButton("Preview")
        self._toggle_btn.setObjectName("icon_btn")
        self._toggle_btn.setFixedWidth(72)
        self._toggle_btn.clicked.connect(self._toggle)
        toolbar.addStretch()
        toolbar.addWidget(self._toggle_btn)
        layout.addLayout(toolbar)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("Write in Markdown…")
        self._editor.textChanged.connect(lambda: self.content_changed.emit(self._editor.toPlainText()))
        layout.addWidget(self._editor)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.hide()
        layout.addWidget(self._browser)

    def _toggle(self):
        self._preview_mode = not self._preview_mode
        if self._preview_mode:
            html = render_md(self._editor.toPlainText())
            self._browser.setHtml(html)
            self._editor.hide()
            self._browser.show()
            self._toggle_btn.setText("Edit")
        else:
            self._browser.hide()
            self._editor.show()
            self._toggle_btn.setText("Preview")

    def set_content(self, text: str) -> None:
        self._editor.setPlainText(text)

    def get_content(self) -> str:
        return self._editor.toPlainText()
