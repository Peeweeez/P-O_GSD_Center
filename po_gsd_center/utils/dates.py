from datetime import date, datetime
from typing import Optional


def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now().isoformat(timespec="seconds")


def days_until(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        d = date.fromisoformat(date_str)
        return (d - date.today()).days
    except ValueError:
        return None


def countdown_label(date_str: Optional[str]) -> str:
    n = days_until(date_str)
    if n is None:
        return ""
    if n < 0:
        return f"{abs(n)}d overdue"
    if n == 0:
        return "Due today"
    if n == 1:
        return "Due tomorrow"
    return f"Due in {n}d"


def fmt_date_short(date_str: Optional[str]) -> str:
    if not date_str:
        return ""
    try:
        d = date.fromisoformat(date_str)
        return d.strftime("%b %d")
    except ValueError:
        return date_str


def fmt_date_full(date_str: Optional[str]) -> str:
    if not date_str:
        return ""
    try:
        d = date.fromisoformat(date_str)
        return d.strftime("%B %d, %Y")
    except ValueError:
        return date_str


def is_overdue(date_str: Optional[str]) -> bool:
    n = days_until(date_str)
    return n is not None and n < 0


def week_dates() -> list:
    """Return list of 7 date objects starting from today."""
    today = date.today()
    return [date.fromordinal(today.toordinal() + i) for i in range(7)]
