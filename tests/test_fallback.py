"""Unit tests for offline heuristic fallback matcher and language detection."""
import pytest
from src.engine.fallback import detect_language_heuristic, run_fallback_matcher


@pytest.fixture
def sample_knowledge():
    return [
        {
            "id": "newcastle",
            "names": {
                "en": "Newcastle Disease",
                "ha": "Cutar Newcastle",
                "yo": "Àrùn Newcastle"
            },
            "severity": "CRITICAL",
            "symptoms": {
                "en": ["twisted neck", "green diarrhea"],
                "ha": ["karkacewar wuya", "zawo mai kore"]
            },
            "advice": {
                "en": "Isolate immediately.",
                "ha": "Ware YANZU."
            },
            "escalation_words": ["twisted neck", "karkacewar wuya", "sudden death"]
        },
        {
            "id": "coccidiosis",
            "names": {
                "en": "Coccidiosis",
                "ha": "Coccidiosis"
            },
            "severity": "HIGH",
            "symptoms": {
                "en": ["bloody droppings", "weight loss"],
                "ha": ["zawo mai jini", "rasa nauyi"]
            },
            "advice": {
                "en": "Give AMPROLIUM.",
                "ha": "Ba AMPROLIUM."
            },
            "escalation_words": ["bloody droppings", "zawo mai jini"]
        }
    ]


def test_detect_language_heuristic():
    assert detect_language_heuristic("My chickens have green poop") == "en"
    assert detect_language_heuristic("Kaji na suna zawo mai jini ko mutu") == "ha"
    assert detect_language_heuristic("Dem dey shit blood and no fit chop") == "pcm"
    assert detect_language_heuristic("Adìẹ mi n ya gbẹ́ ẹjẹ") == "yo"


def test_fallback_matcher_critical_emergency(sample_knowledge):
    result = run_fallback_matcher("My birds have a twisted neck and green diarrhea", sample_knowledge)
    assert result["language"] == "en"
    assert result["disease_id"] == "newcastle"
    assert result["urgency"] == "RED"
    assert result["escalate"] is True
    assert "EMERGENCY (Offline Mode)" in result["answer"]


def test_fallback_matcher_high_severity(sample_knowledge):
    result = run_fallback_matcher("They have bloody droppings and weight loss", sample_knowledge)
    assert result["disease_id"] == "coccidiosis"
    assert result["urgency"] == "ORANGE"
    assert result["escalate"] is False
    assert "AMPROLIUM" in result["answer"]


def test_fallback_matcher_hausa(sample_knowledge):
    result = run_fallback_matcher("Kaji na suna zawo mai jini sosai", sample_knowledge)
    assert result["language"] == "ha"
    assert result["disease_id"] == "coccidiosis"
    assert "AMPROLIUM" in result["answer"]


def test_fallback_matcher_unknown_condition(sample_knowledge):
    result = run_fallback_matcher("My chickens are playing around happily", sample_knowledge)
    assert result["disease_id"] is None
    assert result["urgency"] == "GREEN"
    assert result["escalate"] is False
    assert "I cannot identify the condition" in result["answer"]
