from typing import Optional
from ...db.connection import get_connection
from ...models.entities import Link
from ...utils.uid import uid
from ...utils.dates import now_str


def _row_to_link(row) -> Link:
    return Link(
        id=row["id"],
        project_id=row["project_id"],
        url=row["url"],
        title=row["title"],
        category=row["category"],
        description=row["description"],
        created_at=row["created_at"],
    )


def create(
    project_id: str,
    url: str,
    title: str = "",
    category: str = "",
    description: str = "",
) -> Link:
    l = Link(id=uid(), project_id=project_id, url=url, title=title,
              category=category, description=description, created_at=now_str())
    conn = get_connection()
    conn.execute(
        "INSERT INTO links(id,project_id,url,title,category,description,created_at) VALUES(?,?,?,?,?,?,?)",
        (l.id, l.project_id, l.url, l.title, l.category, l.description, l.created_at),
    )
    conn.commit()
    return l


def get(link_id: str) -> Optional[Link]:
    row = get_connection().execute("SELECT * FROM links WHERE id=?", (link_id,)).fetchone()
    return _row_to_link(row) if row else None


def get_all(project_id: str) -> list[Link]:
    rows = get_connection().execute(
        "SELECT * FROM links WHERE project_id=? ORDER BY created_at DESC", (project_id,)
    ).fetchall()
    return [_row_to_link(r) for r in rows]


def update(l: Link) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE links SET url=?,title=?,category=?,description=? WHERE id=?",
        (l.url, l.title, l.category, l.description, l.id),
    )
    conn.commit()


def delete(link_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM links WHERE id=?", (link_id,))
    conn.commit()
