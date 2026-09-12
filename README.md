# VOICE-AGENT

Advanced local-first AI Voice Counsellor for admissions, lead qualification, FAQ answering, counselling booking, and future telephony.

## What is included

- English, Telugu, and Hindi conversation routing
- Code-mixed Indian speech support through multilingual STT/LLM
- Local speech-to-text with faster-whisper
- Local LLM through Ollama
- Knowledge-grounded answers using local embeddings + FAISS
- Lead capture and counselling workflow abstractions
- Browser microphone transport over WebSocket
- Local TTS adapter using Piper
- SQLite development database
- Docker and CI configuration
- Telephony-ready service boundaries for a later Asterisk/FreeSWITCH integration

## Architecture

```text
Browser microphone
      |
      v
 FastAPI backend
      |
      +--> Voice pipeline
      |      +--> browser audio capture
      |      +--> faster-whisper STT
      |      +--> conversation manager
      |      +--> Ollama LLM
      |      +--> RAG knowledge retrieval
      |      +--> Piper local TTS
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

## Local stack

- Python 3.11+
- FastAPI + Uvicorn
- faster-whisper
- Ollama
- sentence-transformers + FAISS
- Piper TTS
- SQLite

The core development stack does not require paid API keys.

## Setup

### 1. Clone

```bash
git clone https://github.com/Harishhhh11/VOICE-AGENT.git
cd VOICE-AGENT
```

### 2. Python environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Ollama

Install Ollama and pull the configured model:

```bash
ollama pull qwen3:8b
```

Make sure Ollama is running before testing chat.

### 4. Piper TTS

Install a local Piper runtime and download a compatible `.onnx` voice model. Store the model somewhere outside the repository and set its absolute path in `.env`:

```text
TTS_PROVIDER=piper
TTS_VOICE=C:\\path\\to\\your\\piper-voice.onnx
```

For Telugu/Hindi/Indian-English voice quality, choose an appropriate Piper voice model for the target language. The application does not download voices automatically.

### 5. Environment

Copy `.env.example` to `.env` and adjust values as needed.

### 6. Start backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Serve the browser UI

Use any local static server for `web/`. For example:

```bash
python -m http.server 5500 --directory web
```

Then open:

```text
http://127.0.0.1:5500
```

Allow microphone access when prompted.

## Test endpoints

Open FastAPI docs:

```text
http://localhost:8000/docs
```

Health:

```text
http://localhost:8000/health
```

Voice capabilities:

```text
http://localhost:8000/api/voice-capabilities
```

## Knowledge base

Put institution-specific documents in `knowledge_base/`. Replace the sample data with real course, fees, eligibility, placement, admission, batch, and contact information before using the system with prospects.

The assistant is instructed not to invent institution-specific facts. Missing facts should be escalated instead of guessed.

## Production path

Development:

```text
Laptop -> local AI services -> browser
```

Public web:

```text
Domain -> reverse proxy -> FastAPI -> local/model services -> database
```

Telephony later:

```text
SIP/telephony provider -> Asterisk/FreeSWITCH -> voice service -> AI pipeline
```

Open-source software does not remove telecom carrier/SIP charges.

## Security

Never commit API keys, database credentials, customer data, recordings, `.env` files, or local model files.

Audio uploads are bounded by `MAX_AUDIO_MB` and only a small allow-list of common media extensions is accepted.

## Status

The repository contains the deployable application foundation and local voice loop. Before public production use, validate the chosen local STT/LLM/TTS models on the actual server hardware, replace the sample knowledge base, move production data to PostgreSQL, add authentication/rate limits, and configure HTTPS/reverse proxying.
