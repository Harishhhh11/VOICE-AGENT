from __future__ import annotations

import shutil
from pathlib import Path

from app.config import get_settings


def main() -> int:
    settings = get_settings()
    print(f"project={Path.cwd()}")
    print(f"piper={shutil.which('piper') or 'NOT FOUND'}")
    print(f"ollama={shutil.which('ollama') or 'NOT FOUND'}")
    print(f"tts_provider={settings.tts_provider}")
    for language, configured in {
        "en": settings.tts_voice_en,
        "hi": settings.tts_voice_hi,
        "te": settings.tts_voice_te,
    }.items():
        path = Path(configured).resolve()
        print(f"tts_{language}={path} exists={path.is_file()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
