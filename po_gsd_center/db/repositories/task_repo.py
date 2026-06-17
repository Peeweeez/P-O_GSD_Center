import json
from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Task, Subtask, Comment
from ...utils.uid import uid
from ...utils.dates import now_str, today_str, days_until

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATUS_ORDER = {"todo": 0, "in-progress": 1, "blocked": 2, "review": 3, "done": 4}


def _row_to_task(row) -> Task:
    subtasks = [Subtask(**s) for s in json.loads(row["subtasks"] or "[]")]
    comments = [Comment(**c) for c in json.loads(row["comments"] or "[]")]
    return Task(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        status=row["status"],
        due_date=row["due_date"],
        stakeholder=row["stakeholder"],
        recurrence=row["recurrence"],
        quadrant=row["quadrant"],
        pinned=bool(row["pinned"]),
        subtasks=subtasks,
        comments=comments,
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )


def create(
    project_id: str,
    title: str,
    *,
    description: str = "",
    priority: str = "medium",
    status: str = "todo",
    due_date: Optional[str] = None,
    stakeholder: str = "",
    recurrence: str = "none",
    quadrant: str = "none",
    pinned: bool = False,
) -> Task:
    t = Task(
        id=uid(),
        project_id=project_id,
        title=title,
        description=description,
        priority=priority,
        status=status,
        due_date=due_date,
        stakeholder=stakeholder,
        recurrence=recurrence,
        quadrant=quadrant,
        pinned=pinned,
        created_at=now_str(),
    )
    _insert(t)
    return t


def _insert(t: Task) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO tasks(id,project_id,title,description,priority,status,due_date,
           stakeholder,recurrence,quadrant,pinned,subtasks,comments,created_at,completed_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            t.id, t.project_id, t.title, t.description, t.priority, t.status,
            t.due_date, t.stakeholder, t.recurrence, t.quadrant, int(t.pinned),
            json.dumps([vars(s) for s in t.subtasks]),
            json.dumps([vars(c) for c in t.comments]),
            t.created_at, t.completed_at,
        ),
    )
    conn.commit()


def get(task_id: str) -> Optional[Task]:
    row = get_connection().execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def get_all(
    project_id: str,
    *,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    stakeholder_filter: Optional[str] = None,
    sort: str = "smart",
) -> list[Task]:
    sql = "SELECT * FROM tasks WHERE project_id=?"
    params: list = [project_id]
    if status_filter and status_filter != "all":
        sql += " AND status=?"
        params.append(status_filter)
    if priority_filter and priority_filter != "all":
        sql += " AND priority=?"
        params.append(priority_filter)
    if stakeholder_filter:
        sql += " AND LOWER(stakeholder) LIKE ?"
        params.append(f"%{stakeholder_filter.lower()}%")
    rows = get_connection().execute(sql, params).fetchall()
    tasks = [_row_to_task(r) for r in rows]
    return _sort(tasks, sort)


def _sort(tasks: list[Task], sort: str) -> list[Task]:
    today = today_str()

    def smart_key(t: Task):
        overdue = t.due_date and t.due_date < today and t.status != "done"
        prio = PRIORITY_ORDER.get(t.priority, 99)
        due_days = days_until(t.due_date) if t.due_date else 9999
        return (0 if t.pinned else 1, 0 if overdue else 1, prio, due_days)

    if sort == "smart":
        return sorted(tasks, key=smart_key)
    if sort == "priority":
        return sorted(tasks, key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.created_at))
    if sort == "dueDate":
        return sorted(tasks, key=lambda t: (t.due_date or "9999", t.created_at))
    if sort == "alpha":
        return sorted(tasks, key=lambda t: t.title.lower())
    if sort == "created":
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    return tasks


def get_for_quadrant(project_id: str, quadrant: str) -> list[Task]:
    rows = get_connection().execute(
        "SELECT * FROM tasks WHERE project_id=? AND quadrant=? AND status!='done'",
        (project_id, quadrant),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_for_date(project_id: str, date_str: str) -> list[Task]:
    rows = get_connection().execute(
        "SELECT * FROM tasks WHERE project_id=? AND due_date=?",
        (project_id, date_str),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def update(t: Task) -> None:
    conn = get_connection()
    conn.execute(
        """UPDATE tasks SET title=?,description=?,priority=?,status=?,due_date=?,
           stakeholder=?,recurrence=?,quadrant=?,pinned=?,subtasks=?,comments=?,
           completed_at=? WHERE id=?""",
        (
            t.title, t.description, t.priority, t.status, t.due_date,
            t.stakeholder, t.recurrence, t.quadrant, int(t.pinned),
            json.dumps([vars(s) for s in t.subtasks]),
            json.dumps([vars(c) for c in t.comments]),
            t.completed_at, t.id,
        ),
    )
    conn.commit()


def delete(task_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()


def bulk_delete(task_ids: list[str]) -> None:
    conn = get_connection()
    placeholders = ",".join("?" * len(task_ids))
    conn.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", task_ids)
    conn.commit()


def bulk_set_status(task_ids: list[str], status: str) -> None:
    conn = get_connection()
    completed_at = now_str() if status == "done" else None
    placeholders = ",".join("?" * len(task_ids))
    conn.execute(
        f"UPDATE tasks SET status=?, completed_at=? WHERE id IN ({placeholders})",
        [status, completed_at] + task_ids,
    )
    conn.commit()


def bulk_set_priority(task_ids: list[str], priority: str) -> None:
    conn = get_connection()
    placeholders = ",".join("?" * len(task_ids))
    conn.execute(
        f"UPDATE tasks SET priority=? WHERE id IN ({placeholders})",
        [priority] + task_ids,
    )
    conn.commit()


def mark_done(task: Task) -> Optional[Task]:
    """Mark done and return a new recurrence task if applicable."""
    from datetime import date, timedelta

    task.status = "done"
    task.completed_at = now_str()
    update(task)

    if task.recurrence == "none" or not task.due_date:
        return None

    try:
        d = date.fromisoformat(task.due_date)
    except ValueError:
        return None

    deltas = {"daily": 1, "weekly": 7, "biweekly": 14, "monthly": 30}
    delta_days = deltas.get(task.recurrence, 0)
    if not delta_days:
        return None

    new_due = (d + timedelta(days=delta_days)).isoformat()
    next_task = create(
        task.project_id,
        task.title,
        description=task.description,
        priority=task.priority,
        status="todo",
        due_date=new_due,
        stakeholder=task.stakeholder,
        recurrence=task.recurrence,
        quadrant=task.quadrant,
    )
    return next_task


def get_all_projects_tasks(project_ids: list[str]) -> list[Task]:
    if not project_ids:
        return []
    placeholders = ",".join("?" * len(project_ids))
    rows = get_connection().execute(
        f"SELECT * FROM tasks WHERE project_id IN ({placeholders})", project_ids
    ).fetchall()
    return [_row_to_task(r) for r in rows]
