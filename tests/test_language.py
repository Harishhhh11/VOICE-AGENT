from app.main import detect_text_language


def test_detect_english_text():
    assert detect_text_language("Hello, how are you?", "auto") == "en"


def test_detect_hindi_script():
    assert detect_text_language("नमस्ते, आप कैसे हैं?", "auto") == "hi"


def test_detect_telugu_script():
    assert detect_text_language("నమస్కారం, ఎలా ఉన్నారు?", "auto") == "te"


def test_explicit_language_wins():
    assert detect_text_language("hello", "te") == "te"
