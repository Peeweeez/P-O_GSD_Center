from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Deadline
from ...utils.uid import uid
from ...utils.dates import now_str, today_str


def _row_to_deadline(row) -> Deadline:
    return Deadline(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        date=row["date"],
        end_date=row["end_date"],
        description=row["description"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
    )


def create(
    project_id: str,
    title: str,
    date: str,
    end_date: Optional[str] = None,
    description: str = "",
) -> Deadline:
    d = Deadline(id=uid(), project_id=project_id, title=title, date=date,
                  end_date=end_date, description=description, created_at=now_str())
    conn = get_connection()
    conn.execute(
        "INSERT INTO deadlines(id,project_id,title,date,end_date,description,completed,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (d.id, d.project_id, d.title, d.date, d.end_date, d.description, 0, d.created_at),
    )
    conn.commit()
    return d


def get(deadline_id: str) -> Optional[Deadline]:
    row = get_connection().execute("SELECT * FROM deadlines WHERE id=?", (deadline_id,)).fetchone()
    return _row_to_deadline(row) if row else None


def get_all(project_id: str) -> list[Deadline]:
    rows = get_connection().execute(
        "SELECT * FROM deadlines WHERE project_id=? ORDER BY date ASC", (project_id,)
    ).fetchall()
    return [_row_to_deadline(r) for r in rows]


def get_upcoming(project_id: str, limit: int = 5) -> list[Deadline]:
    today = today_str()
    rows = get_connection().execute(
        "SELECT * FROM deadlines WHERE project_id=? AND completed=0 AND date>=? ORDER BY date ASC LIMIT ?",
        (project_id, today, limit),
    ).fetchall()
    return [_row_to_deadline(r) for r in rows]


def get_for_date_range(project_id: str, start: str, end: str) -> list[Deadline]:
    rows = get_connection().execute(
        "SELECT * FROM deadlines WHERE project_id=? AND date<=? AND (end_date IS NULL OR end_date>=?)",
        (project_id, end, start),
    ).fetchall()
    return [_row_to_deadline(r) for r in rows]


def update(d: Deadline) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE deadlines SET title=?,date=?,end_date=?,description=?,completed=? WHERE id=?",
        (d.title, d.date, d.end_date, d.description, int(d.completed), d.id),
    )
    conn.commit()


def delete(deadline_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM deadlines WHERE id=?", (deadline_id,))
    conn.commit()
