"""
globalshelf_view.py — Workspace-wide shelf (ideas, links, snippets).
Fixed project_id = "__global"
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QApplication, QMessageBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from ...db.repositories import idea_repo, link_repo, snippet_repo
from ...models.entities import Idea, Link, Snippet
from ...utils.search import rebuild_index
from ..widgets.toast import show_toast

# Reuse the dialogs and row builders from the per-project views
from .ideas_view import _IdeaDialog, _make_idea_row
from .links_view import _LinkDialog, _SnippetDialog, _make_link_row, _make_snippet_row


GLOBAL_ID = "__global"


def _section_header(title: str, on_add) -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(title)
    lbl.setObjectName("section_title")
    row.addWidget(lbl)
    row.addStretch()
    add_btn = QPushButton("+")
    add_btn.setObjectName("icon_btn")
    add_btn.setFixedSize(28, 28)
    add_btn.setToolTip(f"Add to {title}")
    add_btn.clicked.connect(on_add)
    row.addWidget(add_btn)
    return row


class GlobalShelfView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(0)

        title_lbl = QLabel("Global Shelf")
        title_lbl.setObjectName("section_title")
        title_font = QFont()
        title_font.setPointSize(16)
        title_lbl.setFont(title_font)
        root.addWidget(title_lbl)

        sub_lbl = QLabel("Workspace-wide ideas, links and snippets — not tied to any project.")
        sub_lbl.setObjectName("muted")
        sub_lbl.setStyleSheet("margin-bottom: 16px;")
        root.addWidget(sub_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        container = QWidget()
        self._content = QVBoxLayout(container)
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(20)
        scroll.setWidget(container)

        # ── Ideas section ─────────────────────────────────────────────
        ideas_wrap = QFrame()
        ideas_wrap.setObjectName("card")
        ideas_vbox = QVBoxLayout(ideas_wrap)
        ideas_vbox.setContentsMargins(14, 12, 14, 12)
        ideas_vbox.setSpacing(6)
        ideas_vbox.addLayout(_section_header("Ideas", self._on_new_idea))

        self._ideas_list = QVBoxLayout()
        self._ideas_list.setSpacing(4)
        ideas_vbox.addLayout(self._ideas_list)
        self._content.addWidget(ideas_wrap)

        # ── Links section ─────────────────────────────────────────────
        links_wrap = QFrame()
        links_wrap.setObjectName("card")
        links_vbox = QVBoxLayout(links_wrap)
        links_vbox.setContentsMargins(14, 12, 14, 12)
        links_vbox.setSpacing(6)
        links_vbox.addLayout(_section_header("Links", self._on_new_link))

        self._links_list = QVBoxLayout()
        self._links_list.setSpacing(4)
        links_vbox.addLayout(self._links_list)
        self._content.addWidget(links_wrap)

        # ── Snippets section ──────────────────────────────────────────
        snip_wrap = QFrame()
        snip_wrap.setObjectName("card")
        snip_vbox = QVBoxLayout(snip_wrap)
        snip_vbox.setContentsMargins(14, 12, 14, 12)
        snip_vbox.setSpacing(6)
        snip_vbox.addLayout(_section_header("Snippets", self._on_new_snippet))

        self._snip_list = QVBoxLayout()
        self._snip_list.setSpacing(4)
        snip_vbox.addLayout(self._snip_list)
        self._content.addWidget(snip_wrap)

        self._content.addStretch()

    # ── public API ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._populate_ideas()
        self._populate_links()
        self._populate_snippets()

    # ── clear helpers ───────────────────────────────────────────────────

    def _clear_section(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ── Ideas ───────────────────────────────────────────────────────────

    def _populate_ideas(self):
        self._clear_section(self._ideas_list)
        ideas = idea_repo.get_all(GLOBAL_ID, show_archived=False)
        if not ideas:
            lbl = QLabel("No ideas yet.")
            lbl.setObjectName("muted")
            self._ideas_list.addWidget(lbl)
            return
        for idea in ideas:
            row = _make_idea_row(
                idea,
                on_archive=lambda _=idea: self._on_archive_idea(_),
                on_convert=lambda: None,  # no task conversion on global shelf
                on_edit=lambda _=idea: self._on_edit_idea(_),
                on_delete=lambda _=idea: self._on_delete_idea(_),
            )
            self._ideas_list.addWidget(row)

    def _on_new_idea(self):
        dlg = _IdeaDialog(GLOBAL_ID, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            idea_repo.create(
                GLOBAL_ID,
                title=data["title"],
                body=data["body"],
                tags=data["tags"],
                due_date=data["due_date"],
            )
            rebuild_index(GLOBAL_ID)
            self._populate_ideas()
            show_toast(self.window(), "Idea saved", "success")

    def _on_edit_idea(self, idea: Idea):
        dlg = _IdeaDialog(GLOBAL_ID, idea=idea, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            idea.title = data["title"]
            idea.body = data["body"]
            idea.tags = data["tags"]
            idea.due_date = data["due_date"]
            idea_repo.update(idea)
            rebuild_index(GLOBAL_ID)
            self._populate_ideas()
            show_toast(self.window(), "Idea updated", "success")

    def _on_archive_idea(self, idea: Idea):
        idea.archived = not idea.archived
        idea_repo.update(idea)
        self._populate_ideas()
        label = "archived" if idea.archived else "unarchived"
        show_toast(self.window(), f"Idea {label}", "info")

    def _on_delete_idea(self, idea: Idea):
        reply = QMessageBox.question(
            self, "Delete Idea", "Delete this idea?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            idea_repo.delete(idea.id)
            rebuild_index(GLOBAL_ID)
            self._populate_ideas()
            show_toast(self.window(), "Idea deleted", "info")

    # ── Links ───────────────────────────────────────────────────────────

    def _populate_links(self):
        self._clear_section(self._links_list)
        links = link_repo.get_all(GLOBAL_ID)
        if not links:
            lbl = QLabel("No links yet.")
            lbl.setObjectName("muted")
            self._links_list.addWidget(lbl)
            return
        for lnk in links:
            row = _make_link_row(
                lnk,
                on_open=lambda _=lnk: QDesktopServices.openUrl(QUrl(_.url)),
                on_edit=lambda _=lnk: self._on_edit_link(_),
                on_delete=lambda _=lnk: self._on_delete_link(_),
            )
            self._links_list.addWidget(row)

    def _on_new_link(self):
        dlg = _LinkDialog(GLOBAL_ID, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            link_repo.create(
                GLOBAL_ID,
                url=data["url"],
                title=data["title"],
                category=data["category"],
                description=data["description"],
            )
            rebuild_index(GLOBAL_ID)
            self._populate_links()
            show_toast(self.window(), "Link saved", "success")

    def _on_edit_link(self, link: Link):
        dlg = _LinkDialog(GLOBAL_ID, link=link, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            link.url = data["url"]
            link.title = data["title"]
            link.category = data["category"]
            link.description = data["description"]
            link_repo.update(link)
            rebuild_index(GLOBAL_ID)
            self._populate_links()
            show_toast(self.window(), "Link updated", "success")

    def _on_delete_link(self, link: Link):
        reply = QMessageBox.question(
            self, "Delete Link", "Delete this link?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            link_repo.delete(link.id)
            rebuild_index(GLOBAL_ID)
            self._populate_links()
            show_toast(self.window(), "Link deleted", "info")

    # ── Snippets ──────────────────────────────────────────────────────

    def _populate_snippets(self):
        self._clear_section(self._snip_list)
        snippets = snippet_repo.get_all(GLOBAL_ID)
        if not snippets:
            lbl = QLabel("No snippets yet.")
            lbl.setObjectName("muted")
            self._snip_list.addWidget(lbl)
            return
        for snip in snippets:
            row = _make_snippet_row(
                snip,
                on_copy=lambda _=snip: self._on_copy_snippet(_),
                on_edit=lambda _=snip: self._on_edit_snippet(_),
                on_delete=lambda _=snip: self._on_delete_snippet(_),
            )
            self._snip_list.addWidget(row)

    def _on_new_snippet(self):
        dlg = _SnippetDialog(GLOBAL_ID, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            snippet_repo.create(
                GLOBAL_ID,
                label=data["label"],
                text=data["text"],
            )
            rebuild_index(GLOBAL_ID)
            self._populate_snippets()
            show_toast(self.window(), "Snippet saved", "success")

    def _on_edit_snippet(self, snippet: Snippet):
        dlg = _SnippetDialog(GLOBAL_ID, snippet=snippet, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            snippet.label = data["label"]
            snippet.text = data["text"]
            snippet_repo.update(snippet)
            rebuild_index(GLOBAL_ID)
            self._populate_snippets()
            show_toast(self.window(), "Snippet updated", "success")

    def _on_delete_snippet(self, snippet: Snippet):
        reply = QMessageBox.question(
            self, "Delete Snippet", "Delete this snippet?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            snippet_repo.delete(snippet.id)
            rebuild_index(GLOBAL_ID)
            self._populate_snippets()
            show_toast(self.window(), "Snippet deleted", "info")

    def _on_copy_snippet(self, snippet: Snippet):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(snippet.text or "")
        show_toast(self.window(), "Copied!", "success")
