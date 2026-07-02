import os
import uvicorn

if __name__ == "__main__":
    # Reliably read PORT environment variable set by Railway/Cloud providers, defaulting to 7860 for Hugging Face Spaces
    port_str = os.getenv("PORT", "7860")
    try:
        port = int(port_str)
    except ValueError:
        port = 7860
        
    print(f"🚀 Starting Agricare AI Engine on 0.0.0.0:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port)
