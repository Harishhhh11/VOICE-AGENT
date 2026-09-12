from __future__ import annotations

import asyncio
from pathlib import Path


class TextToSpeech:
    """Local-first TTS adapter.

    Piper is the default concrete engine because it runs locally and exposes a
    simple CLI. The voice field is the local Piper model path.
    """

    def __init__(self, provider: str = "piper", voice: str = "") -> None:
        self.provider = provider.lower().strip()
        self.voice = voice

    @property
    def available(self) -> bool:
        if self.provider in {"", "placeholder", "none"}:
            return False
        return self.provider == "piper" and bool(self.voice) and Path(self.voice).exists()

    async def synthesize_wav(self, text: str, output_path: str | Path) -> dict:
        text = text.strip()
        if not text:
            raise ValueError("Text cannot be empty")
        if not self.available:
            return {"available": False, "provider": self.provider, "path": None}
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        if self.provider == "piper":
            return await asyncio.to_thread(self._piper, text, output)
        raise RuntimeError(f"Unsupported TTS provider: {self.provider}")

    def _piper(self, text: str, output: Path) -> dict:
        import subprocess

        command = ["piper", "--model", self.voice, "--output_file", str(output)]
        result = subprocess.run(
            command,
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(error or "Piper TTS failed")
        return {"available": True, "provider": "piper", "path": str(output)}
