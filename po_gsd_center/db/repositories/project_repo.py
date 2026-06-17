import json
from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Project
from ...utils.uid import uid
from ...utils.dates import now_str

GLOBAL_ID = "__global"


def _row_to_project(row) -> Project:
    return Project(
        id=row["id"],
        name=row["name"],
        color=row["color"],
        status=row["status"],
        archived=bool(row["archived"]),
        created_at=row["created_at"],
    )


def ensure_global_shelf() -> None:
    conn = get_connection()
    exists = conn.execute("SELECT 1 FROM projects WHERE id=?", (GLOBAL_ID,)).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO projects(id,name,color,status,archived,created_at) VALUES(?,?,?,?,?,?)",
            (GLOBAL_ID, "Global Shelf", "#6366f1", "active", 0, now_str()),
        )
        conn.commit()


def create(name: str, color: str = "#3b82f6", status: str = "active") -> Project:
    p = Project(id=uid(), name=name, color=color, status=status, created_at=now_str())
    conn = get_connection()
    conn.execute(
        "INSERT INTO projects(id,name,color,status,archived,created_at) VALUES(?,?,?,?,?,?)",
        (p.id, p.name, p.color, p.status, int(p.archived), p.created_at),
    )
    conn.commit()
    return p


def get(project_id: str) -> Optional[Project]:
    row = get_connection().execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    return _row_to_project(row) if row else None


def get_all(include_archived: bool = True, include_global: bool = False) -> list[Project]:
    conn = get_connection()
    sql = "SELECT * FROM projects WHERE id != ?"
    params: list = [GLOBAL_ID]
    if not include_archived:
        sql += " AND archived=0"
    sql += " ORDER BY created_at ASC"
    rows = conn.execute(sql, params).fetchall()
    projects = [_row_to_project(r) for r in rows]
    if include_global:
        g = get(GLOBAL_ID)
        if g:
            projects.insert(0, g)
    return projects


def update(p: Project) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE projects SET name=?,color=?,status=?,archived=? WHERE id=?",
        (p.name, p.color, p.status, int(p.archived), p.id),
    )
    conn.commit()


def delete(project_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()


def get_stats(project_id: str) -> dict:
    conn = get_connection()
    from ...utils.dates import today_str

    today = today_str()
    total = conn.execute("SELECT COUNT(*) FROM tasks WHERE project_id=?", (project_id,)).fetchone()[0]
    done = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE project_id=? AND status='done'", (project_id,)
    ).fetchone()[0]
    open_count = total - done
    overdue = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE project_id=? AND status!='done' AND due_date IS NOT NULL AND due_date<?",
        (project_id, today),
    ).fetchone()[0]
    critical = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE project_id=? AND priority='critical' AND status!='done'",
        (project_id,),
    ).fetchone()[0]
    ideas_count = conn.execute(
        "SELECT COUNT(*) FROM ideas WHERE project_id=? AND archived=0", (project_id,)
    ).fetchone()[0]
    completion = int(done / total * 100) if total > 0 else 0

    # Next deadline
    next_dl = conn.execute(
        "SELECT title, date FROM deadlines WHERE project_id=? AND completed=0 AND date>=? ORDER BY date ASC LIMIT 1",
        (project_id, today),
    ).fetchone()

    return {
        "total": total,
        "done": done,
        "open": open_count,
        "overdue": overdue,
        "critical": critical,
        "ideas": ideas_count,
        "completion": completion,
        "next_deadline": dict(next_dl) if next_dl else None,
    }
