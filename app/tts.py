from __future__ import annotations

import asyncio
import io
import wave
from pathlib import Path


class TextToSpeech:
    """Local-first TTS abstraction.

    The backend exposes one stable interface so a local engine can be swapped in
    without changing the conversation pipeline. When no local engine is
    configured, it returns an explicit unavailable result instead of pretending
    audio was generated.
    """

    def __init__(self, provider: str = "placeholder", voice: str = "") -> None:
        self.provider = provider.lower().strip()
        self.voice = voice

    @property
    def available(self) -> bool:
        if self.provider in {"", "placeholder", "none"}:
            return False
        if self.provider == "piper":
            return bool(self.voice)
        if self.provider == "indicf5":
            return bool(self.voice)
        return False

    async def synthesize_wav(self, text: str, output_path: str | Path) -> dict:
        """Synthesize speech to a WAV file using the selected local provider."""
        text = text.strip()
        if not text:
            raise ValueError("Text cannot be empty")
        if not self.available:
            return {"available": False, "provider": self.provider, "path": None}

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if self.provider == "piper":
            return await asyncio.to_thread(self._piper, text, output)
        if self.provider == "indicf5":
            return await asyncio.to_thread(self._indicf5, text, output)
        raise RuntimeError(f"Unsupported TTS provider: {self.provider}")

    def _piper(self, text: str, output: Path) -> dict:
        import subprocess

        command = ["piper", "--model", self.voice, "--output_file", str(output)]
        result = subprocess.run(command, input=text.encode("utf-8"), capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
        return {"available": True, "provider": "piper", "path": str(output)}

    def _indicf5(self, text: str, output: Path) -> dict:
        """Adapter hook for IndicF5 deployments.

        IndicF5 installations differ in their runtime wrapper/model path, so the
        repo keeps the integration boundary here. The adapter intentionally fails
        clearly until a local model path is configured.
        """
        raise RuntimeError(
            "IndicF5 provider selected but its runtime adapter is not configured. "
            "Set TTS_PROVIDER=piper for a CLI-based local engine or implement the "
            "IndicF5 adapter in app/tts.py for your installed checkpoint."
        )


# Tiny helper useful for tests and clients expecting a WAV container.
def empty_wav_bytes(sample_rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"")
    return buffer.getvalue()
