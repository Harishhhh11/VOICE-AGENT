from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db, save_lead
from .llm import OllamaClient
from .rag import KnowledgeBase
from .schemas import ChatRequest, ChatResponse, HealthResponse, LeadRequest
from .session import SessionStore
from .stt import SpeechToText

settings = get_settings()
kb = KnowledgeBase()
llm = OllamaClient()
stt = SpeechToText(
    model_name=settings.whisper_model,
    device=settings.whisper_device,
    compute_type=settings.whisper_compute_type,
)
sessions = SessionStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    kb.load()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"name": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        llm_available=await llm.is_available(),
        stt_loaded=stt.loaded,
        knowledge_documents=kb.count,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    conversation = sessions.get(request.session_id)
    context, sources = kb.format_context(request.message)
    try:
        reply = await llm.chat(request.message, context, conversation.history[-12:])
    except Exception:
        reply = (
            "I’m sorry, I’m unable to reach the local AI model right now. "
            "Please make sure Ollama is running and try again."
        )
    conversation.add("user", request.message)
    conversation.add("assistant", reply)
    conversation.language = request.language
    return ChatResponse(session_id=request.session_id, reply=reply, language=request.language, sources=sources)


@app.post("/api/leads")
async def create_lead(request: LeadRequest) -> dict:
    lead_id = save_lead(request)
    return {"success": True, "lead_id": lead_id}


@app.post("/api/knowledge/reload")
async def reload_knowledge() -> dict:
    kb.load()
    return {"success": True, "documents": kb.count}


@app.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "default")
    await websocket.send_json({"type": "ready", "session_id": session_id})
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") != "text":
                await websocket.send_json({"type": "error", "message": "Only JSON text turns are supported in this first browser transport."})
                continue
            user_text = str(message.get("text", "")).strip()
            if not user_text:
                continue
            request = ChatRequest(message=user_text, session_id=session_id, language=message.get("language", "auto"))
            response = await chat(request)
            await websocket.send_json({"type": "assistant", "data": response.model_dump()})
    except WebSocketDisconnect:
        sessions.clear(session_id)
