"""Backwards compatibility wrapper and interactive CLI shell for AgriCareEngine."""
import os
from src.engine.core import AgriCareEngine

__all__ = ["AgriCareEngine"]

if __name__ == "__main__":
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
        test_key = input("🔑 Enter your Gemini API Key to test locally (or press Enter for fallback): ").strip()
        if not test_key:
            test_key = None

    engine = AgriCareEngine(api_key=test_key)

    while True:
        try:
            farmer_query = input("\n👨‍🌾 Farmer Query: ")
            if farmer_query.strip().lower() in ["quit", "exit", "stop"]:
                break
            if not farmer_query.strip():
                continue

            result = engine.process(farmer_query)
            print(f"\n🤖 Recommendation [{result.get('urgency')}]:\n{result.get('answer')}")
            print("─" * 60)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting shell.")
            break
