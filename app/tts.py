from __future__ import annotations

import asyncio
from pathlib import Path


class TextToSpeech:
    """Local Piper TTS with automatic language-specific voice selection."""

    def __init__(
        self,
        provider: str = "piper",
        voices: dict[str, str] | None = None,
    ) -> None:
        self.provider = provider.lower().strip()
        self.voices = {key.lower(): value for key, value in (voices or {}).items() if value}

    def voice_for_language(self, language: str) -> Path | None:
        language = (language or "en").lower().split("-")[0].split("_")[0]
        selected = self.voices.get(language) or self.voices.get("en")
        return Path(selected).resolve() if selected else None

    def available_for_language(self, language: str) -> bool:
        if self.provider in {"", "placeholder", "none"}:
            return False
        if self.provider != "piper":
            return False
        voice = self.voice_for_language(language)
        return bool(voice and voice.exists() and voice.is_file())

    @property
    def available(self) -> bool:
        return any(self.available_for_language(language) for language in self.voices)

    async def synthesize_wav(
        self,
        text: str,
        output_path: str | Path,
        language: str = "en",
    ) -> dict:
        text = text.strip()
        if not text:
            raise ValueError("Text cannot be empty")
        if self.provider != "piper":
            raise RuntimeError(f"Unsupported TTS provider: {self.provider}")

        voice = self.voice_for_language(language)
        if voice is None or not voice.exists():
            return {
                "available": False,
                "provider": self.provider,
                "language": language,
                "voice": str(voice) if voice else None,
                "path": None,
            }

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        return await asyncio.to_thread(self._piper, text, output, voice, language)

    def _piper(self, text: str, output: Path, voice: Path, language: str) -> dict:
        import subprocess

        command = ["piper", "--model", str(voice), "--output_file", str(output)]
        result = subprocess.run(
            command,
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            error = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(error or "Piper TTS failed")
        return {
            "available": True,
            "provider": "piper",
            "language": language,
            "voice": str(voice),
            "path": str(output),
        }
