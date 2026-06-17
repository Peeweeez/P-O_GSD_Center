import sqlite3
import os
from pathlib import Path

_conn: sqlite3.Connection | None = None
_DB_PATH: Path | None = None


def set_db_path(path: Path) -> None:
    global _DB_PATH
    _DB_PATH = path


def get_connection() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if _DB_PATH is None:
            data_dir = Path.home() / ".po_gsd_center"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "data.db"
        else:
            db_path = _DB_PATH
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
        _conn.execute("PRAGMA journal_mode = WAL")
    return _conn


def init_db() -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    conn = get_connection()
    with open(schema_path, "r") as f:
        schema = f.read()
    # Execute statements one by one to handle CREATE VIRTUAL TABLE separately
    statements = [s.strip() for s in schema.split(";") if s.strip()]
    for stmt in statements:
        conn.execute(stmt)
    conn.commit()


def close() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
