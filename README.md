# VOICE-AGENT

Advanced local-first AI Voice Counsellor for admissions, lead qualification, FAQ answering, counselling booking, and future telephony.

## Project goals

- Natural English, Telugu, and Hindi conversations
- Code-mixed Indian speech support
- Local speech-to-text with faster-whisper
- Local LLM through Ollama
- Knowledge-grounded answers with RAG
- Lead capture and counselling workflow
- Browser voice interface first; telephony-ready architecture later
- No mandatory paid API dependency for the core development stack
- Production-ready separation between voice, AI, knowledge, and business logic

## Architecture

```text
Browser microphone
      |
      v
 FastAPI backend
      |
      +--> Voice pipeline
      |      +--> VAD / turn detection
      |      +--> faster-whisper STT
      |      +--> conversation manager
      |      +--> Ollama LLM
      |      +--> RAG knowledge retrieval
      |      +--> local TTS adapter
      |
      +--> Business tools
      |      +--> course details
      |      +--> eligibility
      |      +--> fee details
      |      +--> batches
      |      +--> lead capture
      |      +--> counselling booking
      |      +--> human handoff
      |
      +--> SQLite (development) / PostgreSQL (production)
```

## Current stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic Settings
- faster-whisper
- Ollama
- SQLite for local development
- sentence-transformers + FAISS for local retrieval
- WebSocket browser voice transport

The voice/TTS layer is intentionally adapter-based so a local Indic TTS engine can be plugged in without changing the rest of the application.

## Quick start

1. Install Python 3.11 or newer.
2. Install Ollama and pull a suitable multilingual model, for example:

```bash
ollama pull qwen3:8b
```

3. Clone this repository.
4. Create a virtual environment.
5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Copy `.env.example` to `.env` and adjust values.
7. Start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. Open the web client from `web/index.html` through a local static server.

## Knowledge base

Put institution-specific documents in `knowledge_base/`. The repository includes only a small sample dataset. Replace it with the real course, fees, eligibility, placement, admission, batch, and contact information before using the system for real prospects.

The assistant is instructed not to invent institution-specific facts. Missing facts are escalated rather than guessed.

## Deployment path

Development:

```text
Laptop -> local AI services -> browser
```

Public web deployment:

```text
Domain -> reverse proxy -> FastAPI -> local/model services -> database
```

Telephony later:

```text
SIP/telephony provider -> Asterisk/FreeSWITCH -> voice service -> AI pipeline
```

Telephony carriers and SIP providers may incur separate costs even though the application stack is open source.

## Security

Never commit API keys, database credentials, customer data, recordings, or `.env` files.

## Status

Initial production-oriented scaffold. Replace sample knowledge and tune local model/TTS choices for the target hardware before production rollout.
