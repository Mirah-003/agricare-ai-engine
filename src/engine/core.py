"""Core AgriCareEngine class combining Gemini inference with local RAG fallback."""
import os
import json
import httpx
import requests
from typing import Optional, List, Dict, Any

from .prompts import get_system_prompt
from .fallback import run_fallback_matcher


class AgriCareEngine:
    """
    Conversational AI RAG diagnostic engine for poultry health using 
    Google Gemini 2.5 Flash API with deterministic offline fallback.
    Supports both asynchronous and synchronous inference.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("⚠️ WARNING: GEMINI_API_KEY is not set. Using local RAG fallback engine.")

        # Resolve knowledge_base.json reliably from project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.kb_path = os.path.join(project_root, "data", "knowledge_base.json")
        
        if os.path.exists(self.kb_path):
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.knowledge = json.load(f)
            print(f"✅ Loaded {len(self.knowledge)} diseases from {self.kb_path}")
        else:
            self.knowledge = []
            print(f"⚠️ WARNING: {self.kb_path} not found!")
            
        self.system_prompt = get_system_prompt(self.knowledge)

    def _prepare_payload(self, text: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Prepares API payload with system instructions and chat history."""
        contents = []
        if history:
            for msg in history:
                role = msg.get("role", "user")
                text_content = msg.get("text", "")
                if contents and contents[-1]["role"] == role:
                    contents[-1]["parts"][0]["text"] += "\n\n" + text_content
                else:
                    contents.append({"role": role, "parts": [{"text": text_content}]})

        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"][0]["text"] += "\n\n" + text
        else:
            contents.append({"role": "user", "parts": [{"text": text}]})

        return {
            "system_instruction": {"parts": [{"text": self.system_prompt}]},
            "contents": contents,
            "generationConfig": {"responseMimeType": "application/json"}
        }

    def _parse_response(self, raw_json_str: str) -> Dict[str, Any]:
        """Parses and validates Gemini JSON output."""
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

    def process(self, text: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Synchronous process method using requests for CLI and test compatibility."""
        if not self.api_key:
            res = run_fallback_matcher(text, self.knowledge)
            res["status"] = "fallback"
            return res

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = self._prepare_payload(text, history)

        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return self._parse_response(raw_json_str)
        except Exception as e:
            print(f"❌ Error with Gemini API or JSON parsing: {e}. Falling back to offline matcher...")
            res = run_fallback_matcher(text, self.knowledge)
            res["status"] = "fallback"
            return res

    async def process_async(self, text: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Asynchronous process method using httpx for non-blocking FastAPI execution."""
        if not self.api_key:
            res = run_fallback_matcher(text, self.knowledge)
            res["status"] = "fallback"
            return res

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        payload = self._prepare_payload(text, history)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return self._parse_response(raw_json_str)
        except Exception as e:
            print(f"❌ Async Gemini error or JSON parsing failed: {e}. Falling back to offline matcher...")
            res = run_fallback_matcher(text, self.knowledge)
            res["status"] = "fallback"
            return res
