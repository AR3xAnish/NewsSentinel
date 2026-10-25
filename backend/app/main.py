from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.models.models import *
from app.services.rss_service import rss_service
from app.services.scheduler_service import scheduler_service
from app.api.endpoints import router as api_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Seed default RSS sources
    db = SessionLocal()
    try:
        rss_service.seed_default_sources(db)
    finally:
        db.close()

    # Start APScheduler
    scheduler_service.start()
    
    yield

    # Shutdown
    scheduler_service.shutdown()

app = FastAPI(
    title=settings.APP_NAME,
    description="Local AI News Intelligence Agent for YGF NGO Evaluation. Collects news via RSS, cross-validates claims across independent sources, and generates platform-specific social drafts.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
