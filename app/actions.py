from __future__ import annotations

import re
from dataclasses import dataclass, field

from .database import save_lead
from .rag import KnowledgeBase
from .schemas import LeadRequest


@dataclass
class ProspectState:
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    course_interest: str | None = None
    qualification: str | None = None
    preferred_mode: str | None = None
    notes: list[str] = field(default_factory=list)

    def as_lead(self, session_id: str) -> LeadRequest | None:
        if not self.name or not self.phone:
            return None
        return LeadRequest(
            session_id=session_id,
            name=self.name,
            phone=self.phone,
            email=self.email,
            course_interest=self.course_interest,
            qualification=self.qualification,
            preferred_mode=self.preferred_mode,
            notes=" ".join(self.notes) or None,
        )


PHONE_RE = re.compile(r"(?:\\+?91[\\s-]?)?[6-9]\\d{9}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")


class ActionEngine:
    """Deterministic business actions the LLM can be asked to trigger.

    The LLM should not invent transactional facts. This layer is the source of
    truth for structured lead capture and future CRM/telephony integrations.
    """

    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb
        self.prospects: dict[str, ProspectState] = {}

    def state(self, session_id: str) -> ProspectState:
        return self.prospects.setdefault(session_id, ProspectState())

    def extract_contact(self, session_id: str, text: str) -> ProspectState:
        state = self.state(session_id)
        email = EMAIL_RE.search(text)
        phone = PHONE_RE.search(text)
        if email:
            state.email = email.group(0)
        if phone:
            state.phone = phone.group(0)
        return state

    def save_if_ready(self, session_id: str) -> int | None:
        state = self.state(session_id)
        lead = state.as_lead(session_id)
        if not lead:
            return None
        return save_lead(lead)
