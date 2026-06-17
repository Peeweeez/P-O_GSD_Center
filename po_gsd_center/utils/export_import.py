import json
from datetime import datetime
from pathlib import Path
from ..db.connection import get_connection
from ..db.repositories import project_repo, task_repo, note_repo, deadline_repo, link_repo, idea_repo, snippet_repo


def export_json(path: str | Path) -> None:
    projects = project_repo.get_all(include_archived=True, include_global=True)
    data = {"projects": [], "settings": {}, "exportedAt": datetime.now().isoformat()}

    conn = get_connection()
    settings_rows = conn.execute("SELECT key, value FROM settings").fetchall()
    settings = {r["key"]: r["value"] for r in settings_rows}

    for p in projects:
        proj_dict = {
            "id": p.id,
            "name": p.name,
            "color": p.color,
            "status": p.status,
            "archived": p.archived,
            "createdAt": p.created_at,
            "tasks": [],
            "notes": [],
            "deadlines": [],
            "links": [],
            "ideas": [],
            "snippets": [],
        }
        for t in task_repo.get_all(p.id):
            proj_dict["tasks"].append({
                "id": t.id, "title": t.title, "description": t.description,
                "priority": t.priority, "status": t.status, "dueDate": t.due_date,
                "stakeholder": t.stakeholder, "recurrence": t.recurrence,
                "quadrant": t.quadrant, "pinned": t.pinned,
                "subtasks": [vars(s) for s in t.subtasks],
                "comments": [vars(c) for c in t.comments],
                "createdAt": t.created_at, "completedAt": t.completed_at,
            })
        for n in note_repo.get_all(p.id):
            proj_dict["notes"].append({
                "id": n.id, "title": n.title, "content": n.content,
                "date": n.date, "type": n.type, "createdAt": n.created_at,
            })
        for d in deadline_repo.get_all(p.id):
            proj_dict["deadlines"].append({
                "id": d.id, "title": d.title, "date": d.date, "endDate": d.end_date,
                "description": d.description, "completed": d.completed, "createdAt": d.created_at,
            })
        for l in link_repo.get_all(p.id):
            proj_dict["links"].append({
                "id": l.id, "url": l.url, "title": l.title, "category": l.category,
                "description": l.description, "createdAt": l.created_at,
            })
        for i in idea_repo.get_all(p.id, show_archived=True):
            proj_dict["ideas"].append({
                "id": i.id, "title": i.title, "body": i.body, "tags": i.tags,
                "dueDate": i.due_date, "archived": i.archived, "createdAt": i.created_at,
            })
        for s in snippet_repo.get_all(p.id):
            proj_dict["snippets"].append({
                "id": s.id, "label": s.label, "text": s.text, "createdAt": s.created_at,
            })
        data["projects"].append(proj_dict)

    data["settings"] = settings
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def import_json(path: str | Path) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_connection()
    with conn:
        # Wipe existing data
        for table in ["snippets", "ideas", "links", "deadlines", "notes", "tasks", "projects"]:
            conn.execute(f"DELETE FROM {table}")
        conn.execute("DELETE FROM search_fts")

        for p in data.get("projects", []):
            conn.execute(
                "INSERT OR REPLACE INTO projects(id,name,color,status,archived,created_at) VALUES(?,?,?,?,?,?)",
                (p["id"], p["name"], p.get("color", "#3b82f6"), p.get("status", "active"),
                 int(p.get("archived", False)), p.get("createdAt", "")),
            )
            for t in p.get("tasks", []):
                conn.execute(
                    """INSERT OR REPLACE INTO tasks(id,project_id,title,description,priority,status,
                       due_date,stakeholder,recurrence,quadrant,pinned,subtasks,comments,created_at,completed_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (t["id"], p["id"], t["title"], t.get("description", ""),
                     t.get("priority", "medium"), t.get("status", "todo"),
                     t.get("dueDate"), t.get("stakeholder", ""), t.get("recurrence", "none"),
                     t.get("quadrant", "none"), int(t.get("pinned", False)),
                     json.dumps(t.get("subtasks", [])), json.dumps(t.get("comments", [])),
                     t.get("createdAt", ""), t.get("completedAt")),
                )
            for n in p.get("notes", []):
                conn.execute(
                    "INSERT OR REPLACE INTO notes(id,project_id,title,content,date,type,created_at) VALUES(?,?,?,?,?,?,?)",
                    (n["id"], p["id"], n.get("title", ""), n.get("content", ""),
                     n.get("date"), n.get("type", ""), n.get("createdAt", "")),
                )
            for d in p.get("deadlines", []):
                conn.execute(
                    "INSERT OR REPLACE INTO deadlines(id,project_id,title,date,end_date,description,completed,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (d["id"], p["id"], d["title"], d["date"], d.get("endDate"),
                     d.get("description", ""), int(d.get("completed", False)), d.get("createdAt", "")),
                )
            for l in p.get("links", []):
                conn.execute(
                    "INSERT OR REPLACE INTO links(id,project_id,url,title,category,description,created_at) VALUES(?,?,?,?,?,?,?)",
                    (l["id"], p["id"], l["url"], l.get("title", ""), l.get("category", ""),
                     l.get("description", ""), l.get("createdAt", "")),
                )
            for i in p.get("ideas", []):
                conn.execute(
                    "INSERT OR REPLACE INTO ideas(id,project_id,title,body,tags,due_date,archived,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (i["id"], p["id"], i["title"], i.get("body", ""),
                     json.dumps(i.get("tags", [])), i.get("dueDate"),
                     int(i.get("archived", False)), i.get("createdAt", "")),
                )
            for s in p.get("snippets", []):
                conn.execute(
                    "INSERT OR REPLACE INTO snippets(id,project_id,label,text,created_at) VALUES(?,?,?,?,?)",
                    (s["id"], p["id"], s["label"], s.get("text", ""), s.get("createdAt", "")),
                )

        for k, v in data.get("settings", {}).items():
            conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, str(v)))
