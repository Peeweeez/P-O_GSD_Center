from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Snippet
from ...utils.uid import uid
from ...utils.dates import now_str


def _row_to_snippet(row) -> Snippet:
    return Snippet(
        id=row["id"],
        project_id=row["project_id"],
        label=row["label"],
        text=row["text"],
        created_at=row["created_at"],
    )


def create(project_id: str, label: str, text: str = "") -> Snippet:
    s = Snippet(id=uid(), project_id=project_id, label=label, text=text, created_at=now_str())
    conn = get_connection()
    conn.execute(
        "INSERT INTO snippets(id,project_id,label,text,created_at) VALUES(?,?,?,?,?)",
        (s.id, s.project_id, s.label, s.text, s.created_at),
    )
    conn.commit()
    return s


def get(snippet_id: str) -> Optional[Snippet]:
    row = get_connection().execute("SELECT * FROM snippets WHERE id=?", (snippet_id,)).fetchone()
    return _row_to_snippet(row) if row else None


def get_all(project_id: str) -> list[Snippet]:
    rows = get_connection().execute(
        "SELECT * FROM snippets WHERE project_id=? ORDER BY created_at DESC", (project_id,)
    ).fetchall()
    return [_row_to_snippet(r) for r in rows]


def update(s: Snippet) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE snippets SET label=?,text=? WHERE id=?",
        (s.label, s.text, s.id),
    )
    conn.commit()


def delete(snippet_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM snippets WHERE id=?", (snippet_id,))
    conn.commit()
