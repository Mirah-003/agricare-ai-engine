import os
import requests

class AgriCareEngine:
    """Conversational AI RAG diagnostic engine for poultry health using Gemini (Direct API) with local fallback."""

    def __init__(self, api_key: str = None):
        print("🧠 Initializing Conversational RAG Agricare AI engine...")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ WARNING: GEMINI_API_KEY is not set. Using local RAG fallback engine.")

        import json
        self.kb_path = os.path.join(os.path.dirname(__file__), "data", "knowledge_base.json")
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.knowledge = json.load(f)
            print(f"✅ Loaded {len(self.knowledge)} diseases from {self.kb_path}")
        else:
            self.knowledge = []
            print("⚠️ WARNING: data/knowledge_base.json not found!")

    def fallback_process(self, text: str) -> dict:
        """Fallback symptom matching when Gemini is offline or unavailable."""
        text_lower = text.lower()
        
        # 1. Basic language detection
        lang = "en"
        lang_indicators = {
            "ha": ["kaji", "zawo", "mutu", "hanci", "tari", "kore", "fari", "baki", "ciki", "da"],
            "yo": ["adìẹ", "arun", "gbẹ́", "ẹjẹ", "omi", "ewé", "orí", "enà", "ní", "tó"],
            "ig": ["ọkụkọ", "ọrịa", "nsị", "ọbara", "mmiri", "nri", "isi", "taa", "na", "ndụ"],
            "pcm": ["dey", "wey", "go", "fit", "chop", "sabi", "abeg", "shit", "blood", "body", "dem"]
        }
        import re
        words = set(re.findall(r'\b\w+\b', text_lower))
        for l, indicators in lang_indicators.items():
            if any(ind in words for ind in indicators):
                lang = l
                break
                
        # 2. Simple keyword matching over symptoms
        best_match = None
        max_matches = 0
        for disease in self.knowledge:
            matches = 0
            # Check symptoms in detected language and English
            symptom_list = disease.get("symptoms", {}).get(lang, []) + disease.get("symptoms", {}).get("en", [])
            for symptom in symptom_list:
                if symptom.lower() in text_lower:
                    matches += 2 # higher weight for exact phrase
                else:
                    # check individual word intersection
                    s_words = set(symptom.lower().split())
                    q_words = set(text_lower.split())
                    intersection = q_words.intersection(s_words)
                    if len(intersection) >= 2:
                        matches += 1
            
            # Check escalation words
            for ew in disease.get("escalation_words", []):
                if ew.lower() in text_lower:
                    matches += 3 # highest weight for escalation triggers
                    
            if matches > max_matches:
                max_matches = matches
                best_match = disease
                
        # 3. Formulate the fallback report
        if best_match:
            name = best_match["names"].get(lang, best_match["names"]["en"])
            advice = best_match["advice"].get(lang, best_match["advice"]["en"])
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

    def process(self, text: str, history: list = None) -> dict:
        """Processes user input using Gemini with fallback and conversational memory."""
        if not self.api_key:
            print("⚠️ Gemini Key missing. Using local RAG fallback...")
            res = self.fallback_process(text)
            res["status"] = "fallback"
            return res
            
        import json
        kb_str = json.dumps(self.knowledge, ensure_ascii=False, indent=2)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        system_prompt = (
            "You are Agricare AI, an expert poultry veterinarian for Nigerian smallholder farmers.\n"
            "Your job is to diagnose poultry diseases based on the farmer's query and provide advice using the verified veterinary knowledge base.\n\n"
            f"Here is the verified veterinary knowledge base containing 15 poultry diseases:\n{kb_str}\n\n"
            "Instructions:\n"
            "1. Detect the farmer's language (English, Hausa, Yoruba, Igbo, Nigerian Pidgin).\n"
            "2. Act as a careful veterinary triage assistant. When a farmer first describes a problem, DO NOT immediately diagnose the disease. You MUST first ask 1 or 2 clarifying questions to gather more context (e.g., What is the age of the birds? How long have they been sick? Are there any other symptoms like diarrhea or coughing? Have they been vaccinated?).\n"
            "3. Only after the farmer has answered your clarifying questions and you have enough context should you match their symptoms to the most logical disease in the knowledge base and provide a final diagnosis.\n"
            "4. When asking questions, set `disease_id` and `disease_name` to null, and `urgency` to 'GREEN'.\n"
            "5. If a matching disease is confidently found (after gathering context), you MUST use the verified 'advice' and 'names' from the knowledge base in the farmer's language. If the language isn't explicitly supported, use English.\n"
            "6. Keep your final answer text concise, conversational, polite, and suitable for a WhatsApp/USSD message. Do not overwhelm the user with long blocks of text.\n"
            "7. Triage the severity (only when providing a final diagnosis): \n"
            "   - Set urgency to 'RED' (and 'escalate' to true) if the confidently matched disease has severity 'CRITICAL' or if the user's message describes a fatal emergency (e.g. birds dying rapidly).\n"
            "   - Set urgency to 'ORANGE' if severity is 'HIGH'.\n"
            "   - Set urgency to 'YELLOW' if severity is 'MEDIUM'.\n"
            "   - Set urgency to 'GREEN' for general care / info or when asking clarifying questions.\n"
            "8. Provide your output in JSON format with these exact keys:\n"
            "   - 'language': The detected language code ('en', 'ha', 'yo', 'ig', 'pcm')\n"
            "   - 'disease_id': The ID of the confidently matched disease (or null if asking questions / none matched)\n"
            "   - 'disease_name': The name of the matched disease in the detected language (or null if asking questions)\n"
            "   - 'urgency': 'RED', 'ORANGE', 'YELLOW', or 'GREEN'\n"
            "   - 'escalate': true or false\n"
            "   - 'answer': Your helpful, conversational message to the farmer in their language. Either your clarifying questions OR your final diagnosis/advice.\n\n"
            "Always output raw JSON ONLY. Do not enclose in markdown code blocks."
        )
        
        contents = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                text_content = msg.get("text", "")
                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"][0]["text"] += "\n\n" + text_content
                else:
                    contents.append({"role": role, "parts": [{"text": text_content}]})
        
        # Ensure the final incoming message is also correctly appended/squashed
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"][0]["text"] += "\n\n" + text
        else:
            contents.append({"role": "user", "parts": [{"text": text}]})
        
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            raw_json_str = data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            result = json.loads(raw_json_str)
            return {
                "language": result.get("language", "en"),
                "disease_id": result.get("disease_id"),
                "disease_name": result.get("disease_name"),
                "urgency": result.get("urgency", "GREEN"),
                "escalate": result.get("escalate", False),
                "answer": result.get("answer", "No answer provided."),
                "status": "success"
            }
        except Exception as e:
            print(f"❌ Error with Gemini API or JSON parsing: {e}. Falling back to offline matcher...")
            res = self.fallback_process(text)
            res["status"] = "fallback"
            return res

if __name__ == "__main__":
    # Interactive test session
    print("\n" + "=" * 60)
    print("🐔 POULTRY HEALTH DIAGNOSTIC SYSTEM (Conversational)")
    print("=" * 60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    test_key = os.getenv("GEMINI_API_KEY")
    if not test_key:
        test_key = input("🔑 Enter your Gemini API Key to test locally: ").strip()

    engine = AgriCareEngine(api_key=test_key)

    while True:
        farmer_query = input("\n👨‍🌾 Farmer Query: ")
        if farmer_query.strip().lower() in ["quit", "exit", "stop"]:
            break
        
        result = engine.process(farmer_query)
        print(f"\n🤖 Recommendation:\n{result['answer']}")
        print(f"{'─' * 60}\n")
