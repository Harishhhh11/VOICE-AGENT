from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from .config import get_settings


class KnowledgeBase:
    def __init__(self, root: str = "knowledge_base") -> None:
        self.root = Path(root)
        self.documents: list[dict[str, str]] = []
        self._model = None
        self._matrix = None

    @property
    def count(self) -> int:
        return len(self.documents)

    def _split(self, text: str, source: str) -> list[dict[str, str]]:
        cleaned = re.sub(r"\r\n?", "\n", text).strip()
        if not cleaned:
            return []
        chunks = []
        for block in re.split(r"\n\s*\n", cleaned):
            block = block.strip()
            if not block:
                continue
            if len(block) <= 1200:
                chunks.append({"text": block, "source": source})
                continue
            for start in range(0, len(block), 900):
                chunks.append({"text": block[start:start + 1100], "source": source})
        return chunks

    def load(self) -> None:
        self.documents = []
        self.root.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.root.rglob("*.txt")):
            self.documents.extend(self._split(path.read_text(encoding="utf-8"), str(path)))
        for path in sorted(self.root.rglob("*.json")):
            if path.name.startswith("index"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        text = item.get("text") or item.get("content")
                        if text:
                            self.documents.append({"text": str(text), "source": str(path)})
                    elif isinstance(item, str):
                        self.documents.append({"text": item, "source": str(path)})
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str):
                        self.documents.append({"text": f"{key}: {value}", "source": str(path)})

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(get_settings().embedding_model)
            if self.documents:
                embeddings = self._model.encode(
                    [item["text"] for item in self.documents],
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                self._matrix = np.asarray(embeddings, dtype=np.float32)
        except Exception:
            # RAG remains usable through deterministic lexical fallback when the embedding model
            # cannot be loaded on a small development machine.
            self._model = None
            self._matrix = None

    def search(self, query: str, top_k: int | None = None) -> list[dict[str, str | float]]:
        if not self.documents:
            return []
        k = top_k or get_settings().top_k
        if self._model is not None and self._matrix is not None:
            vector = self._model.encode([query], normalize_embeddings=True, show_progress_bar=False)
            scores = np.asarray(vector, dtype=np.float32) @ self._matrix.T
            order = np.argsort(-scores[0])[:k]
            return [
                {
                    "text": self.documents[int(i)]["text"],
                    "source": self.documents[int(i)]["source"],
                    "score": float(scores[0][int(i)]),
                }
                for i in order
            ]

        tokens = {token.lower() for token in re.findall(r"\w+", query) if len(token) > 2}
        scored = []
        for item in self.documents:
            item_tokens = {token.lower() for token in re.findall(r"\w+", item["text"]) if len(token) > 2}
            overlap = len(tokens & item_tokens)
            scored.append((overlap, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"text": item["text"], "source": item["source"], "score": float(score)}
            for score, item in scored[:k]
            if score > 0
        ]

    def format_context(self, query: str) -> tuple[str, list[str]]:
        results = self.search(query)
        if not results:
            return "", []
        parts = []
        sources = []
        for result in results:
            parts.append(f"SOURCE: {result['source']}\n{result['text']}")
            sources.append(str(result["source"]))
        return "\n\n---\n\n".join(parts), sources
