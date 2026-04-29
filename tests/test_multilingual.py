from pdf_converse.language_support import detect_language, multilingual_keywords, format_multilingual_response

def test_language_detection_english():
    text = "What is the maintenance schedule?"
    lang = detect_language(text)
    assert lang == "en"

def test_language_detection_spanish():
    text = "¿Cuál es el horario de mantenimiento?"
    lang = detect_language(text)
    assert lang == "es"

def test_multilingual_keywords_english():
    keywords = multilingual_keywords("What is the maintenance schedule?", "en")
    assert "maintenance" in keywords
    assert "schedule" in keywords

def test_format_multilingual_response_english():
    response = format_multilingual_response(
        "The filter should be replaced every 6 months",
        [1, 2],
        "en",
        refused=False
    )
    assert "Answer:" in response
    assert "Citations:" in response
    assert "p.1" in response

def test_format_multilingual_response_spanish_refusal():
    response = format_multilingual_response(
        "I can only answer using the provided PDF",
        [],
        "es",
        refused=True
    )
    assert "Respuesta:" in response
    assert "Citas:" in response
