from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class KpiCard(QFrame):
    def __init__(self, label: str, value: str, subtitle: str = "", accent: str = "#3d6b8c", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(140)
        self._accent = accent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(2)

        self._label_w = QLabel(label.upper())
        self._label_w.setObjectName("kpi_label")
        self._value_w = QLabel(value)
        self._value_w.setObjectName("kpi_number")
        self._sub_w = QLabel(subtitle)
        self._sub_w.setObjectName("muted")

        layout.addWidget(self._label_w)
        layout.addWidget(self._value_w)
        if subtitle:
            layout.addWidget(self._sub_w)

        self._apply_border()

    def _apply_border(self):
        self.setStyleSheet(f"""
            QFrame#card {{
                border-left: 4px solid {self._accent};
            }}
        """)

    def set_value(self, value: str) -> None:
        self._value_w.setText(value)

    def set_subtitle(self, subtitle: str) -> None:
        self._sub_w.setText(subtitle)
