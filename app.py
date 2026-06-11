from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from run_agricare import AgriCareEngine

# Load environment variables
load_dotenv()

# 1. Configuration & Security Setup
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# The API key you give to your Django developer
EXPECTED_API_KEY = os.getenv("AGRICARE_API_KEY", "agricare_test_key_123")

def get_api_key(api_key_header: str = Security(api_key_header), request: Request = None):
    query_key = request.query_params.get("key")
    if query_key == EXPECTED_API_KEY:
        return query_key
    if api_key_header == EXPECTED_API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403, 
        detail="Could not validate credentials. Please provide a valid API key via 'X-API-Key' header or '?key=' query parameter."
    )

# 2. Application State & Engine Loading
engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    # Read the Gemini key from the environment (or .env file)
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

# Add CORS middleware for Django integration
# In production, set CORS_ORIGINS env var to restrict allowed origins
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080")
_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# 3. Models
class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, Any]]] = None

class QueryResponse(BaseModel):
    answer: str
    status: str
    language: Optional[str] = None
    disease_id: Optional[str] = None
    disease_name: Optional[str] = None
    urgency: Optional[str] = None
    escalate: Optional[bool] = None

# 4. API Endpoints
@app.get("/")
def read_root():
    return {"message": "Agricare AI API is running. Use /generateContent endpoint for queries."}

@app.post("/generateContent", response_model=QueryResponse)
def generate_content(request: QueryRequest, api_key: str = Depends(get_api_key)):
    """
    Main conversational endpoint. Requires your AGRICARE_API_KEY.
    Returns structured diagnostic JSON with language, disease, urgency, and escalation info.
    """
    try:
        result = engine.process(request.query, request.history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
