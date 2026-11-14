import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.api.auth import router as auth_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.questions import router as questions_router
from backend.app.api.publish import router as publish_router
from backend.app.api.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("questforge")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed default rubrics/admin if needed
    logger.info("Initializing QuestForge database tables...")
    Base.metadata.create_all(bind=engine)
    try:
        from backend.app.seed.seed_data import seed_initial_data
        from backend.app.database import SessionLocal
        db = SessionLocal()
        seed_initial_data(db)
        db.close()
    except Exception as e:
        logger.warning(f"Seed data initialization notice: {e}")
    yield
    logger.info("Shutting down QuestForge...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="QuestForge: AI-driven autonomous coding question generation, sandbox verification & HackerRank publishing engine.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please consult system logs."}
    )

# Include Routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(questions_router)
app.include_router(publish_router)
app.include_router(health_router)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health"
    }
