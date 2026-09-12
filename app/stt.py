from __future__ import annotations

import asyncio
from pathlib import Path


class SpeechToText:
    def __init__(self, model_name: str = "small", device: str = "auto", compute_type: str = "auto") -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._load_lock = asyncio.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    async def load(self) -> None:
        if self._model is not None:
            return
        async with self._load_lock:
            if self._model is not None:
                return
            from faster_whisper import WhisperModel

            def build() -> WhisperModel:
                device = self.device
                compute_type = self.compute_type
                if device == "auto":
                    device = "cpu"
                if compute_type == "auto":
                    compute_type = "int8" if device == "cpu" else "float16"
                return WhisperModel(self.model_name, device=device, compute_type=compute_type)

            self._model = await asyncio.to_thread(build)

    async def transcribe(self, audio_path: str | Path, language: str | None = None) -> dict:
        await self.load()
        if self._model is None:
            raise RuntimeError("STT model failed to load")

        def run() -> dict:
            segments, info = self._model.transcribe(
                str(audio_path),
                language=None if language in (None, "auto", "") else language,
                vad_filter=True,
                beam_size=5,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return {
                "text": text,
                "language": getattr(info, "language", "unknown"),
                "language_probability": float(getattr(info, "language_probability", 0.0)),
            }

        return await asyncio.to_thread(run)
