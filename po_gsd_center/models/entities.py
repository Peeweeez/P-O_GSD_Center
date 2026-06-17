from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Subtask:
    id: str
    title: str
    done: bool = False


@dataclass
class Comment:
    id: str
    text: str
    at: str  # ISO datetime string


@dataclass
class Project:
    id: str
    name: str
    color: str = "#3b82f6"
    status: str = "active"
    archived: bool = False
    created_at: str = ""


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "todo"
    due_date: Optional[str] = None
    stakeholder: str = ""
    recurrence: str = "none"
    quadrant: str = "none"
    pinned: bool = False
    subtasks: list = field(default_factory=list)
    comments: list = field(default_factory=list)
    created_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class Note:
    id: str
    project_id: str
    title: str = ""
    content: str = ""
    date: Optional[str] = None
    type: str = ""
    created_at: str = ""


@dataclass
class Deadline:
    id: str
    project_id: str
    title: str = ""
    date: str = ""
    end_date: Optional[str] = None
    description: str = ""
    completed: bool = False
    created_at: str = ""


@dataclass
class Link:
    id: str
    project_id: str
    url: str = ""
    title: str = ""
    category: str = ""
    description: str = ""
    created_at: str = ""


@dataclass
class Idea:
    id: str
    project_id: str
    title: str = ""
    body: str = ""
    tags: list = field(default_factory=list)
    due_date: Optional[str] = None
    archived: bool = False
    created_at: str = ""


@dataclass
class Snippet:
    id: str
    project_id: str
    label: str = ""
    text: str = ""
    created_at: str = ""


@dataclass
class SearchResult:
    entity_type: str
    project_id: str
    entity_id: str
    title: str
    body: str = ""
