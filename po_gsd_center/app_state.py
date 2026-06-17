from .db.connection import get_connection


DEFAULTS = {
    "active_project_id": "",
    "active_view": "overview",
    "dark_mode": "false",
    "sidebar_collapsed": "false",
    "task_tab": "list",
    "task_sort": "smart",
    "links_tab": "links",
    "show_archived_ideas": "false",
    "cal_year": "",
    "cal_month": "",
}


class AppState:
    def __init__(self):
        self._cache: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        self._cache = {r["key"]: r["value"] for r in rows}

    def get(self, key: str) -> str:
        return self._cache.get(key, DEFAULTS.get(key, ""))

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value
        conn = get_connection()
        conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))
        conn.commit()

    @property
    def active_project_id(self) -> str:
        return self.get("active_project_id")

    @active_project_id.setter
    def active_project_id(self, val: str) -> None:
        self.set("active_project_id", val)

    @property
    def active_view(self) -> str:
        return self.get("active_view")

    @active_view.setter
    def active_view(self, val: str) -> None:
        self.set("active_view", val)

    @property
    def dark_mode(self) -> bool:
        return self.get("dark_mode") == "true"

    @dark_mode.setter
    def dark_mode(self, val: bool) -> None:
        self.set("dark_mode", "true" if val else "false")

    @property
    def sidebar_collapsed(self) -> bool:
        return self.get("sidebar_collapsed") == "true"

    @sidebar_collapsed.setter
    def sidebar_collapsed(self, val: bool) -> None:
        self.set("sidebar_collapsed", "true" if val else "false")

    @property
    def task_tab(self) -> str:
        return self.get("task_tab")

    @task_tab.setter
    def task_tab(self, val: str) -> None:
        self.set("task_tab", val)

    @property
    def task_sort(self) -> str:
        return self.get("task_sort")

    @task_sort.setter
    def task_sort(self, val: str) -> None:
        self.set("task_sort", val)

    @property
    def links_tab(self) -> str:
        return self.get("links_tab")

    @links_tab.setter
    def links_tab(self, val: str) -> None:
        self.set("links_tab", val)

    @property
    def show_archived_ideas(self) -> bool:
        return self.get("show_archived_ideas") == "true"

    @show_archived_ideas.setter
    def show_archived_ideas(self, val: bool) -> None:
        self.set("show_archived_ideas", "true" if val else "false")
