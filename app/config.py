from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Voice Agent"
    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    whisper_model: str = "small"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"
    whisper_language: str = "auto"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    top_k: int = 5

    database_url: str = "sqlite:///./voice_agent.db"
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000"

    tts_provider: str = "placeholder"
    tts_voice: str = ""
    tts_language: str = "auto"
    audio_output_dir: str = "./data/audio"

    max_history_turns: int = 12
    confidence_threshold: float = 0.55
    enable_lead_capture: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
