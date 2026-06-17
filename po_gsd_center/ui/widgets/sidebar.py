from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


NAV_ITEMS = [
    ("overview",    "📊", "Overview"),
    ("tasks",       "✅", "Tasks"),
    ("calendar",    "📅", "Calendar & Deadlines"),
    ("notes",       "📝", "Notes"),
    ("links",       "🔗", "Links & Snippets"),
    ("ideas",       "💡", "Ideas Bank"),
]

WORKSPACE_ITEMS = [
    ("allprojects", "🗂", "All Projects"),
    ("globalshelf", "🌐", "Global Shelf"),
]


class NavButton(QPushButton):
    def __init__(self, view_id: str, icon: str, label: str, collapsed: bool = False):
        super().__init__()
        self.view_id = view_id
        self._icon = icon
        self._label = label
        self._collapsed = collapsed
        self.setObjectName("nav_item")
        self.setCheckable(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(36)
        self._refresh()

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self._refresh()

    def _refresh(self):
        if self._collapsed:
            self.setText(self._icon)
            self.setToolTip(self._label)
        else:
            self.setText(f"  {self._icon}  {self._label}")
            self.setToolTip("")


class Sidebar(QWidget):
    navigate = pyqtSignal(str)
    project_changed = pyqtSignal(str)
    new_project_requested = pyqtSignal()

    EXPANDED_W = 220
    COLLAPSED_W = 48

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._collapsed = False
        self._project_ids: list[str] = []
        self._nav_btns: dict[str, NavButton] = {}

        self.setFixedWidth(self.EXPANDED_W)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(52)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        self._title_label = QLabel("P-O GSD")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self._title_label.setFont(font)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        self._collapse_btn = QPushButton("◀")
        self._collapse_btn.setObjectName("icon_btn")
        self._collapse_btn.setFixedSize(28, 28)
        self._collapse_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self._collapse_btn)
        outer.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        # Project selector
        self._proj_section = QWidget()
        proj_layout = QVBoxLayout(self._proj_section)
        proj_layout.setContentsMargins(8, 8, 8, 4)
        proj_layout.setSpacing(4)
        self._proj_label = QLabel("PROJECT")
        self._proj_label.setObjectName("muted")
        self._proj_label.setStyleSheet("font-size: 10px; font-weight: bold; padding: 0 4px;")
        proj_layout.addWidget(self._proj_label)
        self._proj_combo = QComboBox()
        self._proj_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._proj_combo.currentIndexChanged.connect(self._on_project_changed)
        proj_layout.addWidget(self._proj_combo)
        outer.addWidget(self._proj_section)

        # Nav section label
        nav_label_container = QWidget()
        nav_label_layout = QHBoxLayout(nav_label_container)
        nav_label_layout.setContentsMargins(12, 8, 8, 2)
        self._nav_label = QLabel("VIEWS")
        self._nav_label.setObjectName("muted")
        self._nav_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        nav_label_layout.addWidget(self._nav_label)
        outer.addWidget(nav_label_container)

        # Nav buttons
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(4, 0, 4, 0)
        nav_layout.setSpacing(2)
        for view_id, icon, label in NAV_ITEMS:
            btn = NavButton(view_id, icon, label)
            btn.clicked.connect(lambda _, v=view_id: self.navigate.emit(v))
            nav_layout.addWidget(btn)
            self._nav_btns[view_id] = btn
        outer.addWidget(nav_container)

        # Workspace section
        ws_label_container = QWidget()
        ws_label_layout = QHBoxLayout(ws_label_container)
        ws_label_layout.setContentsMargins(12, 12, 8, 2)
        self._ws_label = QLabel("WORKSPACE")
        self._ws_label.setObjectName("muted")
        self._ws_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        ws_label_layout.addWidget(self._ws_label)
        outer.addWidget(ws_label_container)

        ws_container = QWidget()
        ws_layout = QVBoxLayout(ws_container)
        ws_layout.setContentsMargins(4, 0, 4, 0)
        ws_layout.setSpacing(2)
        for view_id, icon, label in WORKSPACE_ITEMS:
            btn = NavButton(view_id, icon, label)
            btn.clicked.connect(lambda _, v=view_id: self.navigate.emit(v))
            ws_layout.addWidget(btn)
            self._nav_btns[view_id] = btn
        outer.addWidget(ws_container)

        outer.addStretch()

    def set_projects(self, projects: list, active_id: str = "") -> None:
        self._proj_combo.blockSignals(True)
        self._proj_combo.clear()
        self._project_ids = []
        for p in projects:
            self._proj_combo.addItem(p.name)
            self._project_ids.append(p.id)
        if active_id and active_id in self._project_ids:
            self._proj_combo.setCurrentIndex(self._project_ids.index(active_id))
        self._proj_combo.blockSignals(False)

    def set_active_view(self, view_id: str) -> None:
        for vid, btn in self._nav_btns.items():
            btn.set_active(vid == view_id)

    def _on_project_changed(self, idx: int) -> None:
        if 0 <= idx < len(self._project_ids):
            self.project_changed.emit(self._project_ids[idx])

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        target_w = self.COLLAPSED_W if self._collapsed else self.EXPANDED_W

        self._anim = QPropertyAnimation(self, b"minimumWidth")
        self._anim.setDuration(180)
        self._anim.setEndValue(target_w)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

        self._anim2 = QPropertyAnimation(self, b"maximumWidth")
        self._anim2.setDuration(180)
        self._anim2.setEndValue(target_w)
        self._anim2.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim2.start()

        self._title_label.setVisible(not self._collapsed)
        self._proj_label.setVisible(not self._collapsed)
        self._nav_label.setVisible(not self._collapsed)
        self._ws_label.setVisible(not self._collapsed)
        self._collapse_btn.setText("▶" if self._collapsed else "◀")

        for btn in self._nav_btns.values():
            btn.set_collapsed(self._collapsed)

        if self._collapsed:
            self._proj_section.hide()
        else:
            self._proj_section.show()

    def get_active_project_id(self) -> str:
        idx = self._proj_combo.currentIndex()
        if 0 <= idx < len(self._project_ids):
            return self._project_ids[idx]
        return ""
