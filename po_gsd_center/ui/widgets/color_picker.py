from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen
from ..style import PROJECT_COLORS


class ColorPicker(QWidget):
    color_selected = pyqtSignal(str)

    def __init__(self, selected: str = "", parent=None):
        super().__init__(parent)
        self._colors = PROJECT_COLORS
        self._selected = selected or self._colors[0]
        self._size = 28
        self._gap = 8
        cols = 5
        rows = (len(self._colors) + cols - 1) // cols
        w = cols * (self._size + self._gap) - self._gap
        h = rows * (self._size + self._gap) - self._gap
        self.setFixedSize(w, h)

    def selected(self) -> str:
        return self._selected

    def set_selected(self, color: str) -> None:
        self._selected = color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cols = 5
        for i, color in enumerate(self._colors):
            row, col = divmod(i, cols)
            x = col * (self._size + self._gap)
            y = row * (self._size + self._gap)
            rect = QRect(x, y, self._size, self._size)
            painter.setBrush(QColor(color))
            if color == self._selected:
                painter.setPen(QPen(QColor("#1a2130"), 3))
            else:
                painter.setPen(QPen(QColor(color).darker(110), 1))
            painter.drawEllipse(rect)
            if color == self._selected:
                painter.setPen(QPen(QColor("white"), 2))
                cx, cy = x + self._size // 2, y + self._size // 2
                painter.drawLine(cx - 5, cy, cx - 1, cy + 4)
                painter.drawLine(cx - 1, cy + 4, cx + 5, cy - 4)

    def mousePressEvent(self, event) -> None:
        cols = 5
        for i, color in enumerate(self._colors):
            row, col = divmod(i, cols)
            x = col * (self._size + self._gap)
            y = row * (self._size + self._gap)
            rect = QRect(x, y, self._size, self._size)
            if rect.contains(event.pos().toPoint()):
                self._selected = color
                self.update()
                self.color_selected.emit(color)
                break
