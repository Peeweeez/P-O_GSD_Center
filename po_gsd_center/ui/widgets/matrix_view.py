from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDrag, QColor
from ...db.repositories import task_repo
from ...models.entities import Task

QUADRANTS = [
    ("do",       "Do First",  "#fee2e2", "#b91c1c"),
    ("schedule", "Schedule",  "#dbeafe", "#1e40af"),
    ("delegate", "Delegate",  "#fef3c7", "#92400e"),
    ("eliminate","Eliminate", "#f3f4f6", "#374151"),
]


class QuadrantList(QListWidget):
    task_dropped = pyqtSignal(str, str)  # task_id, new_quadrant

    def __init__(self, quadrant_id: str, parent=None):
        super().__init__(parent)
        self.quadrant_id = quadrant_id
        self.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setStyleSheet("border: none; background: transparent;")

    def dropEvent(self, event):
        source = event.source()
        if isinstance(source, QuadrantList) and source is not self:
            item = source.currentItem()
            if item:
                task_id = item.data(Qt.ItemDataRole.UserRole)
                task = task_repo.get(task_id)
                if task:
                    task.quadrant = self.quadrant_id
                    task_repo.update(task)
                    new_item = QListWidgetItem(item.text())
                    new_item.setData(Qt.ItemDataRole.UserRole, task_id)
                    self.addItem(new_item)
                    source.takeItem(source.row(item))
                    event.accept()
                    return
        event.ignore()

    def populate(self, tasks: list[Task]) -> None:
        self.clear()
        for t in tasks:
            item = QListWidgetItem(f"  {'📌 ' if t.pinned else ''}{'●' if t.priority == 'critical' else '·'}  {t.title}")
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            item.setToolTip(t.description[:120] if t.description else "")
            self.addItem(item)


class MatrixView(QWidget):
    task_edit_requested = pyqtSignal(str)  # task_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_id = ""
        self._quad_lists: dict[str, QuadrantList] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        title = QLabel("Eisenhower Priority Matrix")
        title.setObjectName("section_title")
        outer.addWidget(title)

        hint = QLabel("Drag tasks between quadrants. Unassigned tasks appear at the bottom.")
        hint.setObjectName("muted")
        outer.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(8)

        for i, (qid, qlabel, bg, fg) in enumerate(QUADRANTS):
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(f"QFrame#card {{ border-top: 4px solid {fg}; }}")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            header = QLabel(qlabel)
            header.setStyleSheet(f"font-weight: bold; color: {fg}; font-size: 12px;")
            card_layout.addWidget(header)

            qlist = QuadrantList(qid)
            self._quad_lists[qid] = qlist
            qlist.itemDoubleClicked.connect(self._on_item_double_clicked)
            card_layout.addWidget(qlist)

            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)

        outer.addLayout(grid)

        # Unassigned section
        unassigned_frame = QFrame()
        unassigned_frame.setObjectName("card")
        ua_layout = QVBoxLayout(unassigned_frame)
        ua_layout.setContentsMargins(10, 8, 10, 8)
        ua_label = QLabel("Unassigned")
        ua_label.setObjectName("muted")
        ua_label.setStyleSheet("font-size: 11px; font-weight: bold;")
        ua_layout.addWidget(ua_label)
        self._unassigned_list = QuadrantList("none")
        self._unassigned_list.setFixedHeight(80)
        self._unassigned_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        for qlist in self._quad_lists.values():
            self._unassigned_list.task_dropped.connect(lambda tid, qid: None)
        ua_layout.addWidget(self._unassigned_list)
        outer.addWidget(unassigned_frame)

    def set_project_id(self, project_id: str) -> None:
        self._project_id = project_id

    def refresh(self) -> None:
        if not self._project_id:
            return
        for qid, qlist in self._quad_lists.items():
            tasks = task_repo.get_for_quadrant(self._project_id, qid)
            qlist.populate(tasks)
        # Unassigned: tasks with quadrant='none' and status!='done'
        unassigned = [
            t for t in task_repo.get_all(self._project_id)
            if t.quadrant == "none" and t.status != "done"
        ]
        self._unassigned_list.populate(unassigned)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_edit_requested.emit(task_id)
