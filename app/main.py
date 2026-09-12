from __future__ import annotations

import base64
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .actions import ActionEngine
from .config import get_settings
from .database import init_db, save_lead
from .llm import OllamaClient
from .rag import KnowledgeBase
from .schemas import ChatRequest, ChatResponse, HealthResponse, LeadRequest
from .session import SessionStore
from .stt import SpeechToText
from .tts import TextToSpeech

settings = get_settings()
kb = KnowledgeBase()
llm = OllamaClient()
stt = SpeechToText(
    model_name=settings.whisper_model,
    device=settings.whisper_device,
    compute_type=settings.whisper_compute_type,
)
tts = TextToSpeech(provider=settings.tts_provider, voice=settings.tts_voice)
sessions = SessionStore()
actions = ActionEngine(kb)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    kb.load()
    Path(settings.audio_output_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
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


@app.get("/api/voice-capabilities")
async def voice_capabilities() -> dict:
    return {
        "stt": {"provider": "faster-whisper", "loaded": stt.loaded, "model": settings.whisper_model},
        "tts": {"provider": settings.tts_provider, "available": tts.available},
        "languages": ["en", "te", "hi", "auto"],
        "audio_upload": True,
        "streaming_transport": "websocket",
    }


async def answer_text(request: ChatRequest) -> ChatResponse:
    conversation = sessions.get(request.session_id)
    actions.extract_contact(request.session_id, request.message)
    context, sources = kb.format_context(request.message)
    try:
        reply = await llm.chat(request.message, context, conversation.history[-settings.max_history_turns:])
    except Exception:
        reply = (
            "I’m sorry, I’m unable to reach the local AI model right now. "
            "Please make sure Ollama is running and try again."
        )
    conversation.add("user", request.message)
    conversation.add("assistant", reply)
    conversation.language = request.language
    return ChatResponse(session_id=request.session_id, reply=reply, language=request.language, sources=sources)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await answer_text(request)


@app.post("/api/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...), language: str = "auto") -> dict:
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)
    try:
        result = await stt.transcribe(tmp_path, language=language)
        return {"success": True, **result}
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/voice/respond")
async def voice_respond(request: ChatRequest) -> dict:
    response = await answer_text(request)
    audio = None
    if tts.available:
        output = Path(settings.audio_output_dir) / f"{request.session_id.replace('/', '_')}.wav"
        result = await tts.synthesize_wav(response.reply, output)
        if result.get("available") and result.get("path"):
            audio = f"/api/voice/audio/{output.name}"
    return {"success": True, "data": response.model_dump(), "audio_url": audio}


@app.get("/api/voice/audio/{filename}")
async def voice_audio(filename: str):
    safe = Path(filename).name
    path = Path(settings.audio_output_dir) / safe
    if not path.exists():
        return {"success": False, "error": "Audio not found"}
    return FileResponse(path, media_type="audio/wav", filename=safe)


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
    await websocket.send_json({"type": "ready", "session_id": session_id, "audio_input": True})
    try:
        while True:
            message = await websocket.receive_json()
            kind = message.get("type")
            if kind == "text":
                user_text = str(message.get("text", "")).strip()
            elif kind == "audio_base64":
                raw = base64.b64decode(message.get("data", ""))
                suffix = str(message.get("extension", ".webm"))
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(raw)
                    tmp_path = Path(tmp.name)
                try:
                    result = await stt.transcribe(tmp_path, language=message.get("language", "auto"))
                    user_text = result["text"].strip()
                finally:
                    tmp_path.unlink(missing_ok=True)
            else:
                await websocket.send_json({"type": "error", "message": "Expected text or audio_base64 message."})
                continue

            if not user_text:
                await websocket.send_json({"type": "empty"})
                continue

            request = ChatRequest(message=user_text, session_id=session_id, language=message.get("language", "auto"))
            response = await answer_text(request)
            audio_url = None
            if tts.available:
                output = Path(settings.audio_output_dir) / f"{session_id.replace('/', '_')}.wav"
                result = await tts.synthesize_wav(response.reply, output)
                if result.get("available"):
                    audio_url = f"/api/voice/audio/{output.name}"
            await websocket.send_json({
                "type": "assistant",
                "data": response.model_dump(),
                "transcript": user_text,
                "audio_url": audio_url,
            })
    except WebSocketDisconnect:
        sessions.clear(session_id)
