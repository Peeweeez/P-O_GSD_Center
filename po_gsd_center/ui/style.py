LIGHT = {
    "bg": "#f9f9f9",
    "bg2": "#f0f0f0",
    "card": "#ffffff",
    "border": "#e0e0e0",
    "text": "#1a2130",
    "text_muted": "#6b7280",
    "accent": "#3d6b8c",
    "accent_hover": "#2d5a7a",
    "sidebar_bg": "#ffffff",
    "sidebar_border": "#e8e8e8",
    "sidebar_item_hover": "#f0f4f8",
    "sidebar_item_active": "#e8f0f8",
    "topbar_bg": "#ffffff",
    "topbar_border": "#e8e8e8",
    "input_bg": "#ffffff",
    "input_border": "#d1d5db",
    "badge_critical_bg": "#fee2e2",
    "badge_critical_fg": "#b91c1c",
    "badge_high_bg": "#fef3c7",
    "badge_high_fg": "#92400e",
    "badge_medium_bg": "#dbeafe",
    "badge_medium_fg": "#1e40af",
    "badge_low_bg": "#f3f4f6",
    "badge_low_fg": "#374151",
    "badge_done_bg": "#d1fae5",
    "badge_done_fg": "#065f46",
    "badge_todo_bg": "#f3f4f6",
    "badge_todo_fg": "#374151",
    "badge_inprog_bg": "#dbeafe",
    "badge_inprog_fg": "#1e40af",
    "badge_blocked_bg": "#fee2e2",
    "badge_blocked_fg": "#b91c1c",
    "badge_review_bg": "#fef3c7",
    "badge_review_fg": "#92400e",
    "shadow": "1px 1px 4px rgba(0,0,0,0.08)",
    "radius": "8px",
    "scrollbar_bg": "#f0f0f0",
    "scrollbar_handle": "#c0c0c0",
}

DARK = {
    "bg": "#1c1c1c",
    "bg2": "#242424",
    "card": "#2a2a2a",
    "border": "#3a3a3a",
    "text": "#eceff1",
    "text_muted": "#9ca3af",
    "accent": "#5b8db8",
    "accent_hover": "#4a7aa8",
    "sidebar_bg": "#242424",
    "sidebar_border": "#333333",
    "sidebar_item_hover": "#2e2e2e",
    "sidebar_item_active": "#2a3a4a",
    "topbar_bg": "#242424",
    "topbar_border": "#333333",
    "input_bg": "#333333",
    "input_border": "#444444",
    "badge_critical_bg": "#4c1a1a",
    "badge_critical_fg": "#fca5a5",
    "badge_high_bg": "#4c3a0a",
    "badge_high_fg": "#fde68a",
    "badge_medium_bg": "#1a2a4c",
    "badge_medium_fg": "#93c5fd",
    "badge_low_bg": "#2a2a2a",
    "badge_low_fg": "#9ca3af",
    "badge_done_bg": "#0a3a2a",
    "badge_done_fg": "#6ee7b7",
    "badge_todo_bg": "#2a2a2a",
    "badge_todo_fg": "#9ca3af",
    "badge_inprog_bg": "#1a2a4c",
    "badge_inprog_fg": "#93c5fd",
    "badge_blocked_bg": "#4c1a1a",
    "badge_blocked_fg": "#fca5a5",
    "badge_review_bg": "#4c3a0a",
    "badge_review_fg": "#fde68a",
    "shadow": "1px 1px 4px rgba(0,0,0,0.4)",
    "radius": "8px",
    "scrollbar_bg": "#2a2a2a",
    "scrollbar_handle": "#444444",
}


def build_qss(theme: dict) -> str:
    t = theme
    return f"""
/* Base */
QWidget {{
    background-color: {t['bg']};
    color: {t['text']};
    font-family: "DM Sans", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {t['bg']};
}}

/* Cards / Frames */
QFrame#card {{
    background-color: {t['card']};
    border: 1px solid {t['border']};
    border-radius: {t['radius']};
}}

/* Sidebar */
QWidget#sidebar {{
    background-color: {t['sidebar_bg']};
    border-right: 1px solid {t['sidebar_border']};
}}

/* Topbar */
QWidget#topbar {{
    background-color: {t['topbar_bg']};
    border-bottom: 1px solid {t['topbar_border']};
}}

/* Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
    background-color: {t['input_bg']};
    color: {t['text']};
    border: 1px solid {t['input_border']};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {t['accent']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t['accent']};
    outline: none;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {t['card']};
    color: {t['text']};
    border: 1px solid {t['border']};
    selection-background-color: {t['accent']};
    selection-color: white;
}}

/* Buttons */
QPushButton {{
    background-color: {t['card']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {t['bg2']};
    border-color: {t['accent']};
}}

QPushButton:pressed {{
    background-color: {t['accent']};
    color: white;
}}

QPushButton#primary {{
    background-color: {t['accent']};
    color: white;
    border: none;
}}

QPushButton#primary:hover {{
    background-color: {t['accent_hover']};
}}

QPushButton#danger {{
    background-color: transparent;
    color: #ef4444;
    border: 1px solid #ef4444;
}}

QPushButton#danger:hover {{
    background-color: #fee2e2;
}}

QPushButton#icon_btn {{
    background: transparent;
    border: none;
    padding: 4px;
    font-size: 16px;
}}

QPushButton#icon_btn:hover {{
    background-color: {t['bg2']};
    border-radius: 4px;
}}

/* Sidebar nav buttons */
QPushButton#nav_item {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: left;
    font-size: 13px;
}}

QPushButton#nav_item:hover {{
    background-color: {t['sidebar_item_hover']};
}}

QPushButton#nav_item[active="true"] {{
    background-color: {t['sidebar_item_active']};
    color: {t['accent']};
    font-weight: bold;
}}

/* Labels */
QLabel#section_title {{
    font-size: 15px;
    font-weight: bold;
    color: {t['text']};
}}

QLabel#muted {{
    color: {t['text_muted']};
    font-size: 12px;
}}

QLabel#kpi_number {{
    font-size: 28px;
    font-weight: bold;
    color: {t['text']};
}}

QLabel#kpi_label {{
    font-size: 11px;
    color: {t['text_muted']};
    text-transform: uppercase;
}}

/* Progress bar */
QProgressBar {{
    background-color: {t['bg2']};
    border-radius: 4px;
    border: none;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {t['accent']};
    border-radius: 4px;
}}

/* List widgets */
QListWidget {{
    background-color: {t['card']};
    border: 1px solid {t['border']};
    border-radius: {t['radius']};
    outline: none;
}}

QListWidget::item {{
    padding: 4px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {t['sidebar_item_active']};
    color: {t['text']};
}}

QListWidget::item:hover {{
    background-color: {t['sidebar_item_hover']};
}}

/* Tab widget */
QTabWidget::pane {{
    border: 1px solid {t['border']};
    border-radius: {t['radius']};
    background-color: {t['card']};
}}

QTabBar::tab {{
    background-color: {t['bg2']};
    color: {t['text_muted']};
    border: 1px solid {t['border']};
    border-bottom: none;
    padding: 6px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background-color: {t['card']};
    color: {t['text']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    color: {t['text']};
}}

/* Scroll bars */
QScrollBar:vertical {{
    background: {t['scrollbar_bg']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {t['scrollbar_handle']};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {t['scrollbar_bg']};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {t['scrollbar_handle']};
    border-radius: 4px;
    min-width: 20px;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* Checkboxes */
QCheckBox {{
    spacing: 6px;
    color: {t['text']};
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {t['input_border']};
    background-color: {t['input_bg']};
}}

QCheckBox::indicator:checked {{
    background-color: {t['accent']};
    border-color: {t['accent']};
}}

/* Date edit */
QDateEdit {{
    background-color: {t['input_bg']};
    color: {t['text']};
    border: 1px solid {t['input_border']};
    border-radius: 6px;
    padding: 6px 8px;
}}

QDateEdit::drop-down {{
    border: none;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {t['border']};
    width: 1px;
}}

/* Scroll area */
QScrollArea {{
    border: none;
    background-color: {t['bg']};
}}

/* Text browser (markdown) */
QTextBrowser {{
    background-color: {t['card']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: {t['radius']};
    padding: 8px;
}}

/* Dialog */
QDialog {{
    background-color: {t['bg']};
}}

/* Group box */
QGroupBox {{
    border: 1px solid {t['border']};
    border-radius: {t['radius']};
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: {t['text']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

/* Tooltip */
QToolTip {{
    background-color: {t['card']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 4px 6px;
}}
"""


PRIORITY_COLORS = {
    "critical": ("#fee2e2", "#b91c1c", "#ef4444"),  # bg, text, dot
    "high":     ("#fef3c7", "#92400e", "#f59e0b"),
    "medium":   ("#dbeafe", "#1e40af", "#3b82f6"),
    "low":      ("#f3f4f6", "#374151", "#9ca3af"),
}

PRIORITY_COLORS_DARK = {
    "critical": ("#4c1a1a", "#fca5a5", "#ef4444"),
    "high":     ("#4c3a0a", "#fde68a", "#f59e0b"),
    "medium":   ("#1a2a4c", "#93c5fd", "#3b82f6"),
    "low":      ("#2a2a2a", "#9ca3af", "#6b7280"),
}

STATUS_COLORS = {
    "todo":        ("#f3f4f6", "#374151"),
    "in-progress": ("#dbeafe", "#1e40af"),
    "blocked":     ("#fee2e2", "#b91c1c"),
    "review":      ("#fef3c7", "#92400e"),
    "done":        ("#d1fae5", "#065f46"),
}

STATUS_COLORS_DARK = {
    "todo":        ("#2a2a2a", "#9ca3af"),
    "in-progress": ("#1a2a4c", "#93c5fd"),
    "blocked":     ("#4c1a1a", "#fca5a5"),
    "review":      ("#4c3a0a", "#fde68a"),
    "done":        ("#0a3a2a", "#6ee7b7"),
}

PROJECT_COLORS = [
    "#3b82f6", "#8b5cf6", "#ec4899", "#ef4444",
    "#f97316", "#eab308", "#22c55e", "#14b8a6",
    "#6366f1", "#0ea5e9",
]
