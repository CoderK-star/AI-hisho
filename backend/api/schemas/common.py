from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    intent: str
    session_id: str
    tools_called: list[str] = []


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None


class ReminderCreate(BaseModel):
    message: str
    remind_at: str
    is_recurring: bool = False
    recurrence_rule: str | None = None


class MemoCreate(BaseModel):
    title: str = ""
    content: str


class MemoryPinRequest(BaseModel):
    content: str
