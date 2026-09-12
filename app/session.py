from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Conversation:
    history: list[dict[str, str]] = field(default_factory=list)
    language: str = "auto"

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        self.history = self.history[-24:]


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Conversation] = {}

    def get(self, session_id: str) -> Conversation:
        return self._sessions.setdefault(session_id, Conversation())

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
