from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(
    title="Interactive Video Study Guide API",
    description="Backend API for generating study guides from videos",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "message": "API is running"}

from backend.routers import guide

app.include_router(guide.router, prefix="/api/guide", tags=["guide"])
