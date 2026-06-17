import json
from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Idea
from ...utils.uid import uid
from ...utils.dates import now_str


def _row_to_idea(row) -> Idea:
    return Idea(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        body=row["body"],
        tags=json.loads(row["tags"] or "[]"),
        due_date=row["due_date"],
        archived=bool(row["archived"]),
        created_at=row["created_at"],
    )


def create(
    project_id: str,
    title: str,
    body: str = "",
    tags: Optional[list] = None,
    due_date: Optional[str] = None,
) -> Idea:
    i = Idea(id=uid(), project_id=project_id, title=title, body=body,
              tags=tags or [], due_date=due_date, created_at=now_str())
    conn = get_connection()
    conn.execute(
        "INSERT INTO ideas(id,project_id,title,body,tags,due_date,archived,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (i.id, i.project_id, i.title, i.body, json.dumps(i.tags), i.due_date, 0, i.created_at),
    )
    conn.commit()
    return i


def get(idea_id: str) -> Optional[Idea]:
    row = get_connection().execute("SELECT * FROM ideas WHERE id=?", (idea_id,)).fetchone()
    return _row_to_idea(row) if row else None


def get_all(project_id: str, show_archived: bool = False) -> list[Idea]:
    sql = "SELECT * FROM ideas WHERE project_id=?"
    params: list = [project_id]
    if not show_archived:
        sql += " AND archived=0"
    sql += " ORDER BY created_at DESC"
    rows = get_connection().execute(sql, params).fetchall()
    return [_row_to_idea(r) for r in rows]


def update(i: Idea) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE ideas SET title=?,body=?,tags=?,due_date=?,archived=? WHERE id=?",
        (i.title, i.body, json.dumps(i.tags), i.due_date, int(i.archived), i.id),
    )
    conn.commit()


def delete(idea_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM ideas WHERE id=?", (idea_id,))
    conn.commit()
