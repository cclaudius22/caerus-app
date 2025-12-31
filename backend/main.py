from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import auth, startups, pitches, qa, subscriptions, question_templates

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


@app.get("/")
async def root():
    return {"message": "Caerus API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
