"""
entry_row.py — Generic reusable row widget for notes, ideas, links, snippets.
"""
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class EntryRow(QFrame):
    """
    A horizontal card row showing: icon/badge (optional), title (bold),
    subtitle (muted), and action buttons.

    Signals
    -------
    edit_clicked(item_id: str)
    delete_clicked(item_id: str)
    """

    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: str = "",
        actions: list | None = None,
        item_id: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._item_id = item_id
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self._hovered = False

        # ── layout ──────────────────────────────────────────────────────────
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 8, 8, 8)
        outer.setSpacing(10)

        # Optional icon/badge label
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFixedWidth(24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            outer.addWidget(icon_lbl)

        # Text column (title + subtitle)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        self._title_lbl.setFont(title_font)
        self._title_lbl.setStyleSheet("background: transparent; border: none;")
        text_col.addWidget(self._title_lbl)

        if subtitle:
            self._sub_lbl = QLabel(subtitle)
            self._sub_lbl.setObjectName("muted")
            self._sub_lbl.setStyleSheet(
                "background: transparent; border: none; font-size: 12px;"
            )
            self._sub_lbl.setWordWrap(False)
            text_col.addWidget(self._sub_lbl)
        else:
            self._sub_lbl = None

        outer.addLayout(text_col, stretch=1)

        # Action buttons
        self._action_btns: list[QPushButton] = []
        if actions:
            for label, callback in actions:
                btn = QPushButton(label)
                btn.setFixedHeight(28)
                btn.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                btn.clicked.connect(callback)
                btn.setVisible(False)      # shown on hover
                outer.addWidget(btn)
                self._action_btns.append(btn)

        self._apply_style(hovered=False)

    # ── public API ──────────────────────────────────────────────────────────

    def set_title(self, title: str) -> None:
        self._title_lbl.setText(title)

    def set_subtitle(self, subtitle: str) -> None:
        if self._sub_lbl:
            self._sub_lbl.setText(subtitle)

    @property
    def item_id(self) -> str:
        return self._item_id

    # ── hover ────────────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style(hovered=True)
        for btn in self._action_btns:
            btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style(hovered=False)
        for btn in self._action_btns:
            btn.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_clicked.emit(self._item_id)
        super().mousePressEvent(event)

    # ── style ────────────────────────────────────────────────────────────────

    def _apply_style(self, hovered: bool) -> None:
        bg = "rgba(0,0,0,0.04)" if hovered else "transparent"
        self.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {bg};
                border-radius: 6px;
                border: 1px solid transparent;
            }}
            QFrame#card:hover {{
                border-color: rgba(0,0,0,0.08);
            }}
            """
        )
