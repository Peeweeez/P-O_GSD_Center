"""
links_view.py — Links & Snippets view for a single project.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTabWidget, QDialog, QFormLayout,
    QLineEdit, QTextEdit, QMessageBox, QApplication, QFrame,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from ...db.repositories import link_repo, snippet_repo
from ...models.entities import Link, Snippet
from ...utils.dates import now_str
from ...utils.search import rebuild_index
from ..widgets.toast import show_toast


# ── Link dialog ──────────────────────────────────────────────────────────────

class _LinkDialog(QDialog):
    def __init__(self, project_id: str, link: Link = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._link = link
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Link" if link else "New Link")
        self._build_ui()
        if link:
            self._populate(link)

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

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://…")
        form.addRow("URL:", self._url_edit)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Display title (optional)")
        form.addRow("Title:", self._title_edit)

        self._cat_edit = QLineEdit()
        self._cat_edit.setPlaceholderText("e.g. reference, resource, tool")
        form.addRow("Category:", self._cat_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Description…")
        self._desc_edit.setFixedHeight(80)
        form.addRow("Description:", self._desc_edit)

        root.addLayout(form)

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

    def _populate(self, link: Link):
        self._url_edit.setText(link.url or "")
        self._title_edit.setText(link.title or "")
        self._cat_edit.setText(link.category or "")
        self._desc_edit.setPlainText(link.description or "")

    def _on_save(self):
        if not self._url_edit.text().strip():
            QMessageBox.warning(self, "Validation", "URL is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "url": self._url_edit.text().strip(),
            "title": self._title_edit.text().strip(),
            "category": self._cat_edit.text().strip(),
            "description": self._desc_edit.toPlainText().strip(),
        }


# ── Snippet dialog ────────────────────────────────────────────────────────────

class _SnippetDialog(QDialog):
    def __init__(self, project_id: str, snippet: Snippet = None, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._snippet = snippet
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setWindowTitle("Edit Snippet" if snippet else "New Snippet")
        self._build_ui()
        if snippet:
            self._populate(snippet)

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

        self._label_edit = QLineEdit()
        self._label_edit.setPlaceholderText("Snippet label…")
        form.addRow("Label:", self._label_edit)

        root.addLayout(form)

        text_lbl = QLabel("Text")
        text_lbl.setObjectName("muted")
        root.addWidget(text_lbl)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Paste snippet content here…")
        self._text_edit.setMinimumHeight(160)
        mono_font = QFont("Courier New", 11)
        self._text_edit.setFont(mono_font)
        root.addWidget(self._text_edit)

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

    def _populate(self, s: Snippet):
        self._label_edit.setText(s.label or "")
        self._text_edit.setPlainText(s.text or "")

    def _on_save(self):
        if not self._label_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Label is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "label": self._label_edit.text().strip(),
            "text": self._text_edit.toPlainText(),
        }


# ── row builders ─────────────────────────────────────────────────────────────

def _make_link_row(link: Link, on_open, on_edit, on_delete) -> QFrame:
    row = QFrame()
    row.setObjectName("card")
    row.setMinimumHeight(52)
    lay = QHBoxLayout(row)
    lay.setContentsMargins(12, 8, 8, 8)
    lay.setSpacing(10)

    icon_lbl = QLabel("🔗")
    icon_lbl.setStyleSheet("background: transparent; border: none;")
    icon_lbl.setFixedWidth(20)
    lay.addWidget(icon_lbl)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    text_col.setContentsMargins(0, 0, 0, 0)

    display = link.title or link.url
    title_lbl = QLabel(display)
    title_font = QFont()
    title_font.setBold(True)
    title_lbl.setFont(title_font)
    title_lbl.setStyleSheet("background: transparent; border: none;")
    title_lbl.setWordWrap(True)
    text_col.addWidget(title_lbl)

    sub_parts = []
    if link.category:
        sub_parts.append(f"[{link.category}]")
    if link.description:
        sub_parts.append(link.description[:60])
    if sub_parts:
        sub_lbl = QLabel("  ".join(sub_parts))
        sub_lbl.setObjectName("muted")
        sub_lbl.setStyleSheet(
            "font-size: 12px; background: transparent; border: none;"
        )
        text_col.addWidget(sub_lbl)

    lay.addLayout(text_col, stretch=1)

    open_btn = QPushButton("Open")
    open_btn.setFixedHeight(28)
    open_btn.clicked.connect(on_open)
    lay.addWidget(open_btn)

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


def _make_snippet_row(snippet: Snippet, on_copy, on_edit, on_delete) -> QFrame:
    row = QFrame()
    row.setObjectName("card")
    row.setMinimumHeight(52)
    lay = QHBoxLayout(row)
    lay.setContentsMargins(12, 8, 8, 8)
    lay.setSpacing(10)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    text_col.setContentsMargins(0, 0, 0, 0)

    label_lbl = QLabel(snippet.label or "(no label)")
    label_font = QFont()
    label_font.setBold(True)
    label_lbl.setFont(label_font)
    label_lbl.setStyleSheet("background: transparent; border: none;")
    text_col.addWidget(label_lbl)

    preview = (snippet.text or "")[:80].replace("\n", " ")
    if len(snippet.text or "") > 80:
        preview += "…"
    preview_lbl = QLabel(preview)
    mono = QFont("Courier New", 11)
    preview_lbl.setFont(mono)
    preview_lbl.setObjectName("muted")
    preview_lbl.setStyleSheet(
        "font-size: 11px; background: transparent; border: none;"
    )
    text_col.addWidget(preview_lbl)
    lay.addLayout(text_col, stretch=1)

    copy_btn = QPushButton("Copy")
    copy_btn.setFixedHeight(28)
    copy_btn.clicked.connect(on_copy)
    lay.addWidget(copy_btn)

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

class LinksView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id: str = ""
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        title_lbl = QLabel("Links & Snippets")
        title_lbl.setObjectName("section_title")
        root.addWidget(title_lbl)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

        # ── Links tab ──────────────────────────────────────────────────
        links_container = QWidget()
        links_root = QVBoxLayout(links_container)
        links_root.setContentsMargins(0, 8, 0, 0)
        links_root.setSpacing(8)

        links_header = QHBoxLayout()
        links_header.addStretch()
        new_link_btn = QPushButton("+ New Link")
        new_link_btn.setObjectName("primary")
        new_link_btn.clicked.connect(self._on_new_link)
        links_header.addWidget(new_link_btn)
        links_root.addLayout(links_header)

        self._links_scroll = QScrollArea()
        self._links_scroll.setWidgetResizable(True)
        self._links_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._links_list_widget = QWidget()
        self._links_list_layout = QVBoxLayout(self._links_list_widget)
        self._links_list_layout.setContentsMargins(0, 0, 0, 0)
        self._links_list_layout.setSpacing(4)
        self._links_list_layout.addStretch()
        self._links_scroll.setWidget(self._links_list_widget)
        links_root.addWidget(self._links_scroll)

        self._tabs.addTab(links_container, "Links")

        # ── Snippets tab ───────────────────────────────────────────────
        snip_container = QWidget()
        snip_root = QVBoxLayout(snip_container)
        snip_root.setContentsMargins(0, 8, 0, 0)
        snip_root.setSpacing(8)

        snip_header = QHBoxLayout()
        snip_header.addStretch()
        new_snip_btn = QPushButton("+ New Snippet")
        new_snip_btn.setObjectName("primary")
        new_snip_btn.clicked.connect(self._on_new_snippet)
        snip_header.addWidget(new_snip_btn)
        snip_root.addLayout(snip_header)

        self._snip_scroll = QScrollArea()
        self._snip_scroll.setWidgetResizable(True)
        self._snip_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._snip_list_widget = QWidget()
        self._snip_list_layout = QVBoxLayout(self._snip_list_widget)
        self._snip_list_layout.setContentsMargins(0, 0, 0, 0)
        self._snip_list_layout.setSpacing(4)
        self._snip_list_layout.addStretch()
        self._snip_scroll.setWidget(self._snip_list_widget)
        snip_root.addWidget(self._snip_scroll)

        self._tabs.addTab(snip_container, "Snippets")

    # ── public API ────────────────────────────────────────────────────────

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def refresh(self) -> None:
        if not self._project_id:
            return
        self._populate_links()
        self._populate_snippets()

    # ── links ─────────────────────────────────────────────────────────────

    def _clear_layout(self, layout) -> None:
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_links(self):
        lay = self._links_list_layout
        self._clear_layout(lay)
        links = link_repo.get_all(self._project_id)
        if not links:
            empty = QLabel("No links yet. Add your first link.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("muted")
            lay.insertWidget(0, empty)
            return
        for lnk in links:
            row = _make_link_row(
                lnk,
                on_open=lambda _=lnk: QDesktopServices.openUrl(QUrl(_. url)),
                on_edit=lambda _=lnk: self._on_edit_link(_),
                on_delete=lambda _=lnk: self._on_delete_link(_),
            )
            lay.insertWidget(lay.count() - 1, row)

    def _on_new_link(self):
        dlg = _LinkDialog(self._project_id, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            link_repo.create(
                self._project_id,
                url=data["url"],
                title=data["title"],
                category=data["category"],
                description=data["description"],
            )
            rebuild_index(self._project_id)
            self._populate_links()
            show_toast(self.window(), "Link saved", "success")

    def _on_edit_link(self, link: Link):
        dlg = _LinkDialog(self._project_id, link=link, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            link.url = data["url"]
            link.title = data["title"]
            link.category = data["category"]
            link.description = data["description"]
            link_repo.update(link)
            rebuild_index(self._project_id)
            self._populate_links()
            show_toast(self.window(), "Link updated", "success")

    def _on_delete_link(self, link: Link):
        reply = QMessageBox.question(
            self, "Delete Link", "Delete this link?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            link_repo.delete(link.id)
            rebuild_index(self._project_id)
            self._populate_links()
            show_toast(self.window(), "Link deleted", "info")

    # ── snippets ──────────────────────────────────────────────────────────

    def _populate_snippets(self):
        lay = self._snip_list_layout
        self._clear_layout(lay)
        snippets = snippet_repo.get_all(self._project_id)
        if not snippets:
            empty = QLabel("No snippets yet. Add your first snippet.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("muted")
            lay.insertWidget(0, empty)
            return
        for snip in snippets:
            row = _make_snippet_row(
                snip,
                on_copy=lambda _=snip: self._on_copy_snippet(_),
                on_edit=lambda _=snip: self._on_edit_snippet(_),
                on_delete=lambda _=snip: self._on_delete_snippet(_),
            )
            lay.insertWidget(lay.count() - 1, row)

    def _on_new_snippet(self):
        dlg = _SnippetDialog(self._project_id, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            snippet_repo.create(
                self._project_id,
                label=data["label"],
                text=data["text"],
            )
            rebuild_index(self._project_id)
            self._populate_snippets()
            show_toast(self.window(), "Snippet saved", "success")

    def _on_edit_snippet(self, snippet: Snippet):
        dlg = _SnippetDialog(self._project_id, snippet=snippet, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            snippet.label = data["label"]
            snippet.text = data["text"]
            snippet_repo.update(snippet)
            rebuild_index(self._project_id)
            self._populate_snippets()
            show_toast(self.window(), "Snippet updated", "success")

    def _on_delete_snippet(self, snippet: Snippet):
        reply = QMessageBox.question(
            self, "Delete Snippet", "Delete this snippet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            snippet_repo.delete(snippet.id)
            rebuild_index(self._project_id)
            self._populate_snippets()
            show_toast(self.window(), "Snippet deleted", "info")

    def _on_copy_snippet(self, snippet: Snippet):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(snippet.text or "")
        show_toast(self.window(), "Copied!", "success")
