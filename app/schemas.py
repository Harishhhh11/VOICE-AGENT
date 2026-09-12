from typing import Literal

from pydantic import BaseModel, Field


Language = Literal["en", "te", "hi", "auto"]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="default", min_length=1, max_length=128)
    language: Language = "auto"


class LeadRequest(BaseModel):
    session_id: str = "default"
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=5, max_length=30)
    email: str | None = Field(default=None, max_length=180)
    course_interest: str | None = Field(default=None, max_length=180)
    qualification: str | None = Field(default=None, max_length=180)
    preferred_mode: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=2000)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    language: str
    sources: list[str] = []


class HealthResponse(BaseModel):
    status: str
    llm_available: bool
    stt_loaded: bool
    knowledge_documents: int
