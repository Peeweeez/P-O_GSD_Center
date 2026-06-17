from ..db.connection import get_connection
from ..models.entities import SearchResult


def rebuild_index(project_id: str) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM search_fts WHERE project_id=?", (project_id,))

    from ..db.repositories import task_repo, note_repo, deadline_repo, link_repo, idea_repo, snippet_repo

    for t in task_repo.get_all(project_id):
        conn.execute(
            "INSERT INTO search_fts(entity_type,project_id,entity_id,title,body) VALUES(?,?,?,?,?)",
            ("task", project_id, t.id, t.title, t.description),
        )
    for n in note_repo.get_all(project_id):
        conn.execute(
            "INSERT INTO search_fts(entity_type,project_id,entity_id,title,body) VALUES(?,?,?,?,?)",
            ("note", project_id, n.id, n.title, n.content),
        )
    for d in deadline_repo.get_all(project_id):
        conn.execute(
            "INSERT INTO search_fts(entity_type,project_id,entity_id,title,body) VALUES(?,?,?,?,?)",
            ("deadline", project_id, d.id, d.title, d.description),
        )
    for l in link_repo.get_all(project_id):
        conn.execute(
            "INSERT INTO search_fts(entity_type,project_id,entity_id,title,body) VALUES(?,?,?,?,?)",
            ("link", project_id, l.id, l.title or l.url, l.description),
        )
    for i in idea_repo.get_all(project_id, show_archived=True):
        conn.execute(
            "INSERT INTO search_fts(entity_type,project_id,entity_id,title,body) VALUES(?,?,?,?,?)",
            ("idea", project_id, i.id, i.title, i.body),
        )
    for s in snippet_repo.get_all(project_id):
        conn.execute(
            "INSERT INTO search_fts(entity_type,project_id,entity_id,title,body) VALUES(?,?,?,?,?)",
            ("snippet", project_id, s.id, s.label, s.text),
        )
    conn.commit()


def query(term: str, limit: int = 20) -> list[SearchResult]:
    if not term or not term.strip():
        return []
    conn = get_connection()
    safe_term = term.replace('"', '""')
    try:
        rows = conn.execute(
            'SELECT entity_type,project_id,entity_id,title,body FROM search_fts WHERE search_fts MATCH ? LIMIT ?',
            (f'"{safe_term}"*', limit),
        ).fetchall()
    except Exception:
        # Fallback to LIKE if FTS syntax fails
        rows = conn.execute(
            'SELECT entity_type,project_id,entity_id,title,body FROM search_fts WHERE title LIKE ? OR body LIKE ? LIMIT ?',
            (f"%{term}%", f"%{term}%", limit),
        ).fetchall()
    return [SearchResult(
        entity_type=r["entity_type"],
        project_id=r["project_id"],
        entity_id=r["entity_id"],
        title=r["title"],
        body=r["body"],
    ) for r in rows]
