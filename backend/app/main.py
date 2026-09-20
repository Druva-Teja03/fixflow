import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.config import settings
from backend.app.database import engine, get_db, check_db_connection, Base
from backend.app.routers import auth, meta, issues, admin, staff, analytics, ai, notifications

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("fixflow")

# Directory paths
CURRENT_FILE = os.path.abspath(__file__)
APP_DIR = os.path.dirname(CURRENT_FILE)
BACKEND_DIR = os.path.dirname(APP_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")

# Ensure uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup verification and cleanup."""
    logger.info("Starting FixFlow backend...")
    db_ok = check_db_connection()
    if db_ok:
        logger.info("Database connection established successfully.")
    else:
        logger.warning("Could not connect to MySQL database during startup check.")
    yield
    logger.info("Shutting down FixFlow backend...")


app = FastAPI(
    title="FixFlow API",
    description="Smart Campus Issue Reporting & Resolution Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(issues.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(staff.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


# Health check endpoint
@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """System health check verifying API and MySQL connectivity."""
    try:
        db.execute(text("SELECT 1;"))
        db_status = "connected"
    except Exception as exc:
        logger.error(f"Health check DB error: {exc}")
        db_status = f"disconnected: {str(exc)}"

    return {
        "status": "ok",
        "app_env": settings.APP_ENV,
        "database": db_status,
        "storage_backend": settings.STORAGE_BACKEND,
        "suggestion_mode": "rules",
        "ai_enabled": settings.AI_ENABLED,
    }


# Static file mounts
# 1. Local image uploads
if os.path.exists(UPLOADS_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# 2. Frontend assets (CSS, JS, subdirectories)
if os.path.exists(FRONTEND_DIR):
    # Explicit route for index / root
    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "FixFlow Frontend ready. Please place index.html in frontend/"}

    # Mount static assets (css, js, html pages)
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
