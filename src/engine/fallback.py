"""Offline heuristic triage and language detection fallback engine."""
import re
from typing import List, Dict, Any


def detect_language_heuristic(text: str) -> str:
    """Detects African poultry farmer language using keyword intersection."""
    text_lower = text.lower()
    lang_indicators = {
        "ha": ["kaji", "zawo", "mutu", "hanci", "tari", "kore", "fari", "baki", "ciki", "da", "sannu"],
        "yo": ["adìẹ", "arun", "gbẹ́", "ẹjẹ", "omi", "ewé", "orí", "enà", "ní", "tó", "pé"],
        "ig": ["ọkụkọ", "ọrịa", "nsị", "ọbara", "mmiri", "nri", "isi", "taa", "na", "ndụ", "ndewo"],
        "pcm": ["dey", "wey", "go", "fit", "chop", "sabi", "abeg", "shit", "blood", "body", "dem", "wetin"]
    }
    words = set(re.findall(r'\b\w+\b', text_lower))
    for lang, indicators in lang_indicators.items():
        if any(ind in words for ind in indicators):
            return lang
    return "en"


def run_fallback_matcher(text: str, knowledge: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Symptom and escalation keyword matcher for 100% offline diagnostic uptime.
    Guarantees structural compliance with API JSON schemas.
    """
    text_lower = text.lower()
    lang = detect_language_heuristic(text)
    
    best_match = None
    max_matches = 0
    
    for disease in knowledge:
        matches = 0
        symptom_list = disease.get("symptoms", {}).get(lang, []) + disease.get("symptoms", {}).get("en", [])
        
        for symptom in symptom_list:
            if symptom.lower() in text_lower:
                matches += 2  # Higher weight for exact symptom phrase match
            else:
                s_words = set(symptom.lower().split())
                q_words = set(text_lower.split())
                if len(q_words.intersection(s_words)) >= 2:
                    matches += 1
                    
        for ew in disease.get("escalation_words", []):
            if ew.lower() in text_lower:
                matches += 3  # Highest weight for critical emergency triggers
                
        if matches > max_matches:
            max_matches = matches
            best_match = disease
            
    if best_match:
        name = best_match["names"].get(lang, best_match["names"].get("en", "Unknown Condition"))
        advice = best_match["advice"].get(lang, best_match["advice"].get("en", "Please consult a veterinarian."))
        severity = best_match.get("severity", "MEDIUM")
        
        urgency = "GREEN"
        escalate = False
        if severity == "CRITICAL":
            urgency = "RED"
            escalate = True
        elif severity == "HIGH":
            urgency = "ORANGE"
            
        templates = {
            "RED": "🚨 EMERGENCY (Offline Mode): ",
            "ORANGE": "⚠️ URGENT (Offline Mode): ",
            "YELLOW": "📋 INFO (Offline Mode): ",
            "GREEN": "✅ ADVICE (Offline Mode): "
        }
        prefix = templates.get(urgency, "📋 ")
        answer = f"{prefix}{name}\n\nAdvice: {advice}\n\n*Note: Running in offline backup mode.*"
        
        return {
            "language": lang,
            "disease_id": best_match["id"],
            "disease_name": name,
            "urgency": urgency,
            "escalate": escalate,
            "answer": answer
        }
        
    return {
        "language": lang,
        "disease_id": None,
        "disease_name": None,
        "urgency": "GREEN",
        "escalate": False,
        "answer": "I cannot identify the condition from my database. Please isolate the sick birds immediately, ensure access to fresh water/warmth, and contact a veterinarian."
    }
