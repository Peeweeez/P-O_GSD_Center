from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Note
from ...utils.uid import uid
from ...utils.dates import now_str


def _row_to_note(row) -> Note:
    return Note(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        content=row["content"],
        date=row["date"],
        type=row["type"],
        created_at=row["created_at"],
    )


def create(
    project_id: str,
    title: str = "",
    content: str = "",
    date: Optional[str] = None,
    type: str = "",
) -> Note:
    n = Note(id=uid(), project_id=project_id, title=title, content=content,
              date=date, type=type, created_at=now_str())
    conn = get_connection()
    conn.execute(
        "INSERT INTO notes(id,project_id,title,content,date,type,created_at) VALUES(?,?,?,?,?,?,?)",
        (n.id, n.project_id, n.title, n.content, n.date, n.type, n.created_at),
    )
    conn.commit()
    return n


def get(note_id: str) -> Optional[Note]:
    row = get_connection().execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
    return _row_to_note(row) if row else None


def get_all(project_id: str) -> list[Note]:
    rows = get_connection().execute(
        "SELECT * FROM notes WHERE project_id=? ORDER BY created_at DESC", (project_id,)
    ).fetchall()
    return [_row_to_note(r) for r in rows]


def update(n: Note) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE notes SET title=?,content=?,date=?,type=? WHERE id=?",
        (n.title, n.content, n.date, n.type, n.id),
    )
    conn.commit()


def delete(note_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
