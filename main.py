import os
import uvicorn

if __name__ == "__main__":
    # Railway's networking proxy defaults to routing traffic to port 8000 if PORT is not passed.
    # We default to 8000 here to perfectly match Railway's internal proxy target (:8000).
    port_str = os.getenv("PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        port = 8000
        
    print(f"🚀 Starting Agricare AI Engine on 0.0.0.0:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port)
