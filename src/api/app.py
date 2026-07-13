"""FastAPI application entrypoint and routes."""
import os
from contextlib import asynccontextmanager
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.models import QueryRequest, QueryResponse
from src.api.security import get_api_key
from src.engine.core import AgriCareEngine

load_dotenv()

engine: Optional[AgriCareEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager initializing the AI engine asynchronously."""
    global engine
    gemini_key = os.getenv("GEMINI_API_KEY")
    engine = AgriCareEngine(api_key=gemini_key)
    yield
    engine = None


app = FastAPI(
    title="Agricare AI API",
    description="Conversational Poultry Health Diagnostic System Backend",
    version="2.0.0",
    lifespan=lifespan
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080")
origins = [o.strip() for o in cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)


@app.get("/")
async def read_root():
    return {"message": "Agricare AI API is running. Use /generateContent endpoint for queries."}


@app.post("/generateContent", response_model=QueryResponse)
async def generate_content(request: QueryRequest, api_key: str = Depends(get_api_key)):
    """
    Main conversational endpoint. Requires valid AGRICARE_API_KEY.
    Uses asynchronous execution (`process_async`) to prevent thread blocking.
    """
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized.")
    try:
        result = await engine.process_async(request.query, request.history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
