"""
allprojects_view.py — All Projects overview / workspace dashboard.
"""
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QGridLayout, QDialog, QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ...db.repositories import project_repo, task_repo
from ...models.entities import Project
from ...utils.dates import today_str
from ..widgets.kpi_card import KpiCard
from ..widgets.project_card import ProjectCard
from ..widgets.project_dialog import ProjectDialog
from ..widgets.toast import show_toast


class AllProjectsView(QScrollArea):
    project_selected = pyqtSignal(str)  # project_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._root = QVBoxLayout(self._container)
        self._root.setContentsMargins(24, 20, 24, 24)
        self._root.setSpacing(16)
        self.setWidget(self._container)

        # ── workspace KPI row ─────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self._kpi_projects = KpiCard("Active Projects", "–", accent="#3b82f6")
        self._kpi_tasks    = KpiCard("Open Tasks",      "–", accent="#22c55e")
        self._kpi_overdue  = KpiCard("Overdue Tasks",   "–", accent="#ef4444")
        self._kpi_pct      = KpiCard("Avg Completion",  "–%", accent="#8b5cf6")
        for kpi in (self._kpi_projects, self._kpi_tasks, self._kpi_overdue, self._kpi_pct):
            kpi_row.addWidget(kpi)
        self._root.addLayout(kpi_row)

        # ── header row ────────────────────────────────────────────────
        header = QHBoxLayout()
        lbl = QLabel("Projects")
        lbl.setObjectName("section_title")
        header.addWidget(lbl)
        header.addStretch()
        new_btn = QPushButton("+ New Project")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._on_new_project)
        header.addWidget(new_btn)
        self._root.addLayout(header)

        # ── active project grid ───────────────────────────────────────
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(16)
        self._root.addWidget(self._grid_widget)

        # ── archived section ──────────────────────────────────────────
        self._archived_group = QGroupBox("Archived Projects")
        self._archived_group.setCheckable(True)
        self._archived_group.setChecked(False)  # collapsed by default
        self._archived_inner = QVBoxLayout(self._archived_group)
        self._archived_inner.setSpacing(8)
        self._archived_grid_widget = QWidget()
        self._archived_grid_layout = QGridLayout(self._archived_grid_widget)
        self._archived_grid_layout.setSpacing(16)
        self._archived_inner.addWidget(self._archived_grid_widget)
        self._root.addWidget(self._archived_group)

        self._root.addStretch()

    # ── public API ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._populate_kpis()
        self._populate_active_grid()
        self._populate_archived_grid()

    # ── helpers ───────────────────────────────────────────────────────────

    def _clear_grid(self, grid: QGridLayout):
        while grid.count():
            item = grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_kpis(self):
        projects = project_repo.get_all(include_archived=False, include_global=False)
        total_open = 0
        total_overdue = 0
        completions = []
        for p in projects:
            stats = project_repo.get_stats(p.id)
            total_open += stats["open"]
            total_overdue += stats["overdue"]
            completions.append(stats["completion"])

        avg_pct = int(sum(completions) / len(completions)) if completions else 0
        self._kpi_projects.set_value(str(len(projects)))
        self._kpi_tasks.set_value(str(total_open))
        self._kpi_overdue.set_value(str(total_overdue))
        self._kpi_pct.set_value(f"{avg_pct}%")

    def _populate_active_grid(self):
        grid = self._grid_layout
        self._clear_grid(grid)
        projects = project_repo.get_all(include_archived=False, include_global=False)

        if not projects:
            empty = QLabel("No active projects yet. Create one to get started!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("muted")
            grid.addWidget(empty, 0, 0)
            return

        cols = 3
        for i, project in enumerate(projects):
            stats = project_repo.get_stats(project.id)
            card = ProjectCard(project, stats)
            card.select_clicked.connect(self.project_selected.emit)
            card.edit_clicked.connect(self._on_edit_project)
            card.archive_clicked.connect(self._on_archive_project)
            grid.addWidget(card, i // cols, i % cols)

    def _populate_archived_grid(self):
        grid = self._archived_grid_layout
        self._clear_grid(grid)
        all_projects = project_repo.get_all(include_archived=True, include_global=False)
        archived = [p for p in all_projects if p.archived]

        if not archived:
            self._archived_group.setVisible(False)
            return

        self._archived_group.setVisible(True)
        self._archived_group.setTitle(f"Archived Projects ({len(archived)})")
        cols = 3
        for i, project in enumerate(archived):
            stats = project_repo.get_stats(project.id)
            card = ProjectCard(project, stats)
            card.select_clicked.connect(self.project_selected.emit)
            card.edit_clicked.connect(self._on_edit_project)
            card.archive_clicked.connect(self._on_archive_project)
            grid.addWidget(card, i // cols, i % cols)

    # ── actions ───────────────────────────────────────────────────────────

    def _on_new_project(self):
        dlg = ProjectDialog(parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            project_repo.create(
                name=data["name"],
                color=data["color"],
                status=data["status"],
            )
            self.refresh()
            show_toast(self.window(), "Project created", "success")

    def _on_edit_project(self, project_id: str):
        project = project_repo.get(project_id)
        if not project:
            return
        dlg = ProjectDialog(project=project, parent=self.window())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            project.name = data["name"]
            project.color = data["color"]
            project.status = data["status"]
            project_repo.update(project)
            self.refresh()
            show_toast(self.window(), "Project updated", "success")

    def _on_archive_project(self, project_id: str):
        project = project_repo.get(project_id)
        if not project:
            return
        action = "unarchive" if project.archived else "archive"
        reply = QMessageBox.question(
            self, f"{action.capitalize()} Project",
            f"Are you sure you want to {action} '{project.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            project.archived = not project.archived
            project_repo.update(project)
            self.refresh()
            label = "archived" if project.archived else "unarchived"
            show_toast(self.window(), f"Project {label}", "info")
