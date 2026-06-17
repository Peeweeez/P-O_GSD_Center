from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor


class Toast(QFrame):
    def __init__(self, parent, message: str, kind: str = "success"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        colors = {
            "success": ("#d1fae5", "#065f46"),
            "error":   ("#fee2e2", "#b91c1c"),
            "info":    ("#dbeafe", "#1e40af"),
        }
        bg, fg = colors.get(kind, ("#d1fae5", "#065f46"))

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {fg}44;
                border-radius: 8px;
                padding: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        icon = {"success": "✓", "error": "✕", "info": "ℹ"}.get(kind, "✓")
        lbl = QLabel(f"{icon}  {message}")
        lbl.setStyleSheet(f"color: {fg}; border: none; background: transparent;")
        layout.addWidget(lbl)

        self.adjustSize()
        self._position()

        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.show()
        self.anim.start()

        QTimer.singleShot(3000, self._fade_out)

    def _position(self) -> None:
        if self.parent():
            p = self.parent()
            x = p.width() - self.width() - 24
            y = p.height() - self.height() - 24
            self.move(x, y)

    def _fade_out(self) -> None:
        self.anim2 = QPropertyAnimation(self, b"windowOpacity")
        self.anim2.setDuration(400)
        self.anim2.setStartValue(1.0)
        self.anim2.setEndValue(0.0)
        self.anim2.finished.connect(self.deleteLater)
        self.anim2.start()


def show_toast(parent, message: str, kind: str = "success") -> Toast:
    return Toast(parent, message, kind)
