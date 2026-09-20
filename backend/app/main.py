import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.config import settings
from backend.app.database import engine, get_db, check_db_connection, Base
from backend.app.models import UploadedImage
from backend.app.routers import auth, meta, issues, admin, staff, analytics, ai, notifications

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("fixflow")

# Directory paths
CURRENT_FILE = os.path.abspath(__file__)
APP_DIR = os.path.dirname(CURRENT_FILE)
BACKEND_DIR = os.path.dirname(APP_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)
PUBLIC_DIR = os.path.join(ROOT_DIR, "public")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
STATIC_DIR = PUBLIC_DIR if os.path.exists(PUBLIC_DIR) else FRONTEND_DIR
UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")

# Ensure uploads directory exists (gracefully ignore on read-only filesystems like Vercel)
try:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
except OSError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup verification and cleanup."""
    logger.info("Starting FixFlow backend...")
    db_ok = check_db_connection()
    if db_ok:
        logger.info("Database connection established successfully.")
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            logger.warning(f"Base.metadata.create_all note: {exc}")
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


# Photo upload serving endpoints (supports database BLOB and local disk fallback)
@app.get("/api/images/{filename}", tags=["Images"])
def get_image_from_api(filename: str, db: Session = Depends(get_db)):
    """Serve uploaded image from database BLOB or local disk."""
    # 1. Query database BLOB
    img = db.query(UploadedImage).filter(UploadedImage.filename == filename).first()
    if img:
        return Response(
            content=img.image_data,
            media_type=img.content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    # 2. Fallback to local disk
    local_path = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(local_path):
        return FileResponse(local_path)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


@app.get("/uploads/{filename}", tags=["Images"])
def get_image_from_uploads(filename: str, db: Session = Depends(get_db)):
    """Serve image from local disk if available, otherwise from database BLOB."""
    # 1. Check local disk first
    local_path = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(local_path):
        return FileResponse(local_path)
    # 2. Check database BLOB
    img = db.query(UploadedImage).filter(UploadedImage.filename == filename).first()
    if img:
        return Response(
            content=img.image_data,
            media_type=img.content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


# Static file serving from public/ (or fallback frontend/)
if os.path.exists(STATIC_DIR):
    # Explicit route for index / root
    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "FixFlow ready. Please place index.html in public/"}

    # Mount static assets (css, js, html pages)
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
