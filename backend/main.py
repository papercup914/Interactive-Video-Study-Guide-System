from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(
    title="Interactive Video Study Guide API",
    description="Backend API for generating study guides from videos",
    version="1.0.0"
)

import os
from fastapi.responses import JSONResponse

# Configure dynamic CORS for frontend access (Vercel & localhost)
raw_cors = os.getenv("CORS_ORIGINS", "*").strip()
if raw_cors == "*" or not raw_cors:
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def block_qa_header_in_prod(request: Request, call_next):
    env = os.getenv("APP_ENV", "").lower()
    is_dev = env in ("development", "dev", "local")
    if not is_dev and request.headers.get("x-qa-test-mode"):
        return JSONResponse(
            status_code=403, 
            content={"detail": "QA test mode is not allowed in production environment."}
        )
    return await call_next(request)

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "message": "API is running"}

from backend.auth import get_current_user
from fastapi import Depends

@app.get("/api/auth/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Protected endpoint to verify user authentication token."""
    return {"status": "ok", "user": current_user}

from backend.routers import guide, discussion, admin

app.include_router(guide.router, prefix="/api/guide", tags=["guide"])
app.include_router(discussion.router, prefix="/api/discussion", tags=["discussion"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
