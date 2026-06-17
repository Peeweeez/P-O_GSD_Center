import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStackedWidget, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QCoreApplication
from PyQt6.QtGui import QKeySequence, QShortcut, QAction

from .widgets.sidebar import Sidebar
from .widgets.topbar import Topbar
from .widgets.context_bar import ContextBar
from .widgets.search_dialog import SearchDialog
from .widgets.toast import show_toast
from .style import LIGHT, DARK, build_qss
from ..app_state import AppState
from ..db.repositories import project_repo
from ..utils.export_import import export_json, import_json
from ..utils.search import rebuild_index


class MainWindow(QMainWindow):
    def __init__(self, state: AppState):
        super().__init__()
        self._state = state
        self._dark = state.dark_mode
        self._current_project_id = state.active_project_id

        self.setWindowTitle("P-O GSD Center")
        self.setMinimumSize(1000, 640)
        self.resize(1280, 780)

        # Apply initial theme
        QApplication.instance().setStyleSheet(build_qss(DARK if self._dark else LIGHT))

        self._build_ui()
        self._connect_signals()
        self._register_shortcuts()
        self._load_initial_state()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        self._topbar = Topbar()
        root.addWidget(self._topbar)

        # Context bar
        self._ctx_bar = ContextBar()
        root.addWidget(self._ctx_bar)

        # Body: sidebar + content
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = Sidebar()
        body_layout.addWidget(self._sidebar)

        # Content stack
        self._stack = QStackedWidget()
        body_layout.addWidget(self._stack)

        root.addWidget(body)

        # Create views (lazy import to avoid circular imports at module load)
        self._views: dict[str, QWidget] = {}
        self._init_views()

    def _init_views(self) -> None:
        from .views.overview_view import OverviewView
        from .views.tasks_view import TasksView
        from .views.calendar_view import CalendarView
        from .views.notes_view import NotesView
        from .views.links_view import LinksView
        from .views.ideas_view import IdeasView
        from .views.allprojects_view import AllProjectsView
        from .views.globalshelf_view import GlobalShelfView

        view_classes = {
            "overview":    OverviewView,
            "tasks":       TasksView,
            "calendar":    CalendarView,
            "notes":       NotesView,
            "links":       LinksView,
            "ideas":       IdeasView,
            "allprojects": AllProjectsView,
            "globalshelf": GlobalShelfView,
        }
        for name, cls in view_classes.items():
            view = cls()
            self._views[name] = view
            self._stack.addWidget(view)

        # Connect view-specific signals
        tasks_view = self._views["tasks"]
        if hasattr(tasks_view, "refresh_needed"):
            tasks_view.refresh_needed.connect(self._refresh_context_bar)

        allproj_view = self._views["allprojects"]
        if hasattr(allproj_view, "project_selected"):
            allproj_view.project_selected.connect(self._on_project_selected_from_card)

        overview_view = self._views["overview"]
        if hasattr(overview_view, "navigate_to"):
            overview_view.navigate_to.connect(self.navigate_to)

    def _connect_signals(self) -> None:
        self._sidebar.navigate.connect(self.navigate_to)
        self._sidebar.project_changed.connect(self._on_project_changed)
        self._sidebar.new_project_requested.connect(self._new_project)

        self._topbar.search_requested.connect(self._open_search)
        self._topbar.export_requested.connect(self._export)
        self._topbar.import_requested.connect(self._import)
        self._topbar.dark_mode_toggled.connect(self._toggle_dark)
        self._topbar.new_project_requested.connect(self._new_project)

    def _register_shortcuts(self) -> None:
        shortcuts = {
            "Ctrl+K": self._open_search,
            "Ctrl+N": self._new_task,
            "Ctrl+I": self._new_idea,
            "Ctrl+L": self._new_link,
            "Ctrl+S": self._new_snippet,
            "Ctrl+D": self._new_deadline,
        }
        for key, slot in shortcuts.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(slot)

        sc_q = QShortcut(QKeySequence("?"), self)
        sc_q.activated.connect(self._show_shortcuts)

    def _load_initial_state(self) -> None:
        # Ensure global shelf exists
        project_repo.ensure_global_shelf()
        self._reload_projects()

        active = self._state.active_project_id
        if not active:
            projects = project_repo.get_all(include_archived=False)
            if projects:
                active = projects[0].id
                self._state.active_project_id = active

        self._current_project_id = active
        self._sidebar.set_projects(
            project_repo.get_all(include_archived=False),
            active_id=active,
        )
        self._set_active_project(active)

        active_view = self._state.active_view or "overview"
        self.navigate_to(active_view)
        self._topbar.set_dark(self._dark)

    def _reload_projects(self) -> None:
        projects = project_repo.get_all(include_archived=False)
        self._sidebar.set_projects(projects, active_id=self._current_project_id)

    def navigate_to(self, view_id: str) -> None:
        if view_id not in self._views:
            return
        self._state.active_view = view_id
        self._sidebar.set_active_view(view_id)
        self._stack.setCurrentWidget(self._views[view_id])

        view = self._views[view_id]

        # Project-scoped views need a project id
        if view_id in ("overview", "tasks", "calendar", "notes", "links", "ideas"):
            if hasattr(view, "set_project_id"):
                view.set_project_id(self._current_project_id)
            self._ctx_bar.show()
            self._refresh_context_bar()
        else:
            self._ctx_bar.hide()
            if view_id == "allprojects":
                if hasattr(view, "refresh"):
                    view.refresh()

        if hasattr(view, "refresh"):
            view.refresh()

        # Update title
        titles = {
            "overview":    "Overview",
            "tasks":       "Tasks",
            "calendar":    "Calendar & Deadlines",
            "notes":       "Notes",
            "links":       "Links & Snippets",
            "ideas":       "Ideas Bank",
            "allprojects": "All Projects",
            "globalshelf": "Global Shelf",
        }
        self._topbar.set_title(titles.get(view_id, view_id.title()))

    def _set_active_project(self, project_id: str) -> None:
        self._current_project_id = project_id
        self._state.active_project_id = project_id

        active_view = self._state.active_view or "overview"
        if active_view in ("overview", "tasks", "calendar", "notes", "links", "ideas"):
            view = self._views.get(active_view)
            if view:
                if hasattr(view, "set_project_id"):
                    view.set_project_id(project_id)
                if hasattr(view, "refresh"):
                    view.refresh()
        self._refresh_context_bar()

    def _on_project_changed(self, project_id: str) -> None:
        self._set_active_project(project_id)
        active_view = self._state.active_view or "overview"
        if active_view not in ("overview", "tasks", "calendar", "notes", "links", "ideas"):
            self.navigate_to("overview")

    def _on_project_selected_from_card(self, project_id: str) -> None:
        self._current_project_id = project_id
        self._state.active_project_id = project_id
        self._reload_projects()
        self._sidebar.set_projects(
            project_repo.get_all(include_archived=False),
            active_id=project_id,
        )
        self.navigate_to("overview")

    def _refresh_context_bar(self) -> None:
        if not self._current_project_id:
            self._ctx_bar.clear()
            return
        project = project_repo.get(self._current_project_id)
        if project:
            stats = project_repo.get_stats(self._current_project_id)
            self._ctx_bar.update_project(project, stats)
        else:
            self._ctx_bar.clear()

    def _open_search(self) -> None:
        dlg = SearchDialog(self)
        dlg.result_selected.connect(self._on_search_result)
        dlg.exec()

    def _on_search_result(self, entity_type: str, project_id: str, entity_id: str) -> None:
        # Navigate to the right project + view
        if project_id != self._current_project_id:
            self._on_project_selected_from_card(project_id)

        view_map = {
            "task":     "tasks",
            "note":     "notes",
            "deadline": "calendar",
            "link":     "links",
            "idea":     "ideas",
            "snippet":  "links",
        }
        self.navigate_to(view_map.get(entity_type, "overview"))

    def _toggle_dark(self) -> None:
        self._dark = not self._dark
        self._state.dark_mode = self._dark
        theme = DARK if self._dark else LIGHT
        QApplication.instance().setStyleSheet(build_qss(theme))
        self._topbar.set_dark(self._dark)

    def _new_project(self) -> None:
        try:
            from .widgets.project_dialog import ProjectDialog
            dlg = ProjectDialog(parent=self)
            if dlg.exec():
                data = dlg.get_data()
                p = project_repo.create(data["name"], data["color"], data["status"])
                # Pre-build search index for new project
                rebuild_index(p.id)
                self._reload_projects()
                self._on_project_selected_from_card(p.id)
                show_toast(self, "Project created!", "success")
        except Exception as e:
            show_toast(self, f"Error: {e}", "error")

    def _new_task(self) -> None:
        if not self._current_project_id:
            return
        self.navigate_to("tasks")
        tasks_view = self._views.get("tasks")
        if tasks_view and hasattr(tasks_view, "_list_view"):
            tasks_view._list_view._quick_input.setFocus()

    def _new_idea(self) -> None:
        if not self._current_project_id:
            return
        self.navigate_to("ideas")
        try:
            from .widgets.idea_dialog import IdeaDialog
            from ..db.repositories import idea_repo
            dlg = IdeaDialog(self._current_project_id, parent=self)
            if dlg.exec():
                idea = dlg.get_idea()
                idea_repo.create(self._current_project_id, idea.title, idea.body, idea.tags, idea.due_date)
                rebuild_index(self._current_project_id)
                view = self._views.get("ideas")
                if view and hasattr(view, "refresh"):
                    view.refresh()
                show_toast(self, "Idea added!", "success")
        except Exception as e:
            show_toast(self, f"Error: {e}", "error")

    def _new_link(self) -> None:
        if not self._current_project_id:
            return
        self.navigate_to("links")
        try:
            from .widgets.link_dialog import LinkDialog
            from ..db.repositories import link_repo
            dlg = LinkDialog(self._current_project_id, parent=self)
            if dlg.exec():
                link = dlg.get_link()
                link_repo.create(self._current_project_id, link.url, link.title, link.category, link.description)
                rebuild_index(self._current_project_id)
                view = self._views.get("links")
                if view and hasattr(view, "refresh"):
                    view.refresh()
                show_toast(self, "Link added!", "success")
        except Exception as e:
            show_toast(self, f"Error: {e}", "error")

    def _new_snippet(self) -> None:
        if not self._current_project_id:
            return
        self.navigate_to("links")
        try:
            from .widgets.snippet_dialog import SnippetDialog
            from ..db.repositories import snippet_repo
            dlg = SnippetDialog(self._current_project_id, parent=self)
            if dlg.exec():
                sn = dlg.get_snippet()
                snippet_repo.create(self._current_project_id, sn.label, sn.text)
                rebuild_index(self._current_project_id)
                view = self._views.get("links")
                if view and hasattr(view, "refresh"):
                    view.refresh()
                show_toast(self, "Snippet added!", "success")
        except Exception as e:
            show_toast(self, f"Error: {e}", "error")

    def _new_deadline(self) -> None:
        if not self._current_project_id:
            return
        self.navigate_to("calendar")
        try:
            from .widgets.deadline_dialog import DeadlineDialog
            from ..db.repositories import deadline_repo
            dlg = DeadlineDialog(self._current_project_id, parent=self)
            if dlg.exec():
                dl = dlg.get_deadline()
                deadline_repo.create(self._current_project_id, dl.title, dl.date, dl.end_date, dl.description)
                rebuild_index(self._current_project_id)
                view = self._views.get("calendar")
                if view and hasattr(view, "refresh"):
                    view.refresh()
                show_toast(self, "Deadline added!", "success")
        except Exception as e:
            show_toast(self, f"Error: {e}", "error")

    def _export(self) -> None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", f"gsd_backup_{ts}.json", "JSON Files (*.json)"
        )
        if path:
            try:
                export_json(path)
                show_toast(self, "Exported successfully!", "success")
            except Exception as e:
                show_toast(self, f"Export failed: {e}", "error")

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Data", "", "JSON Files (*.json)"
        )
        if path:
            reply = QMessageBox.warning(
                self, "Import Data",
                "This will overwrite ALL existing data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    import_json(path)
                    show_toast(self, "Import successful! Reloading…", "success")
                    self._load_initial_state()
                except Exception as e:
                    show_toast(self, f"Import failed: {e}", "error")

    def _show_shortcuts(self) -> None:
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Keyboard Shortcuts")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        rows = [
            ("Ctrl+K", "Open search"),
            ("Ctrl+N", "Focus quick-add task"),
            ("Ctrl+I", "New idea"),
            ("Ctrl+L", "New link"),
            ("Ctrl+S", "New snippet"),
            ("Ctrl+D", "New deadline"),
            ("?",      "Show this dialog"),
            ("Esc",    "Close dialogs"),
        ]
        for key, action in rows:
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(key))
            table.setItem(r, 1, QTableWidgetItem(action))
        layout.addWidget(table)
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            # Let dialogs handle their own Esc
            pass
        super().keyPressEvent(event)
