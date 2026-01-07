import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import auth, startups, pitches, qa, subscriptions, question_templates, admin, talent_pitches, talent_qa, support

# Ensure uploads directory exists
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(os.path.join(UPLOADS_DIR, "avatars"), exist_ok=True)

app = FastAPI(
    title="Caerus API",
    description="Video pitch marketplace for founders and investors",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(startups.router, prefix="/api/v1/startups", tags=["Startups"])
app.include_router(pitches.router, prefix="/api/v1/pitches", tags=["Pitches"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["Q&A"])
app.include_router(subscriptions.router, prefix="/api/v1", tags=["Subscriptions"])
app.include_router(question_templates.router, prefix="/api/v1/questions", tags=["Question Templates"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(talent_pitches.router, prefix="/api/v1/talent-pitches", tags=["Talent Pitches"])
app.include_router(talent_qa.router, prefix="/api/v1/talent-qa", tags=["Talent Q&A"])
app.include_router(support.router, prefix="/api/v1/support", tags=["Support"])

# Mount static files for serving uploaded files (avatars, etc.)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/")
async def root():
    return {"message": "Caerus API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
