import os
import uuid
import logging
from typing import Optional
from fastapi import UploadFile, HTTPException, status

from backend.app.config import settings

logger = logging.getLogger("fixflow.storage")

# Upload constraints
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Megabytes

# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
LOCAL_UPLOADS_DIR = os.path.join(BACKEND_DIR, "uploads")

try:
    os.makedirs(LOCAL_UPLOADS_DIR, exist_ok=True)
except OSError:
    pass


def validate_image_file(file: UploadFile) -> str:
    """
    Validates content-type and returns standard file extension (.jpg, .png, .webp).
    Raises HTTPException(400) if validation fails.
    """
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPEG, PNG, WEBP.",
        )

    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return ext_map.get(content_type, ".jpg")


async def save_uploaded_file(file: Optional[UploadFile], db=None) -> Optional[str]:
    """
    Validates, renames to a UUID, and saves an uploaded photo.
    - If STORAGE_BACKEND == "database": stores image bytes as a BLOB in MySQL
      and returns endpoint URL '/api/images/{filename}'.
    - If STORAGE_BACKEND == "local": writes to local disk and returns '/uploads/{filename}'.
    Returns None if no file was uploaded.
    """
    if not file or not file.filename:
        return None

    ext = validate_image_file(file)

    # Read content and enforce 5 MB limit
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image size exceeds 5 MB limit. Received: {len(content) / (1024 * 1024):.2f} MB.",
        )

    unique_filename = f"{uuid.uuid4().hex}{ext}"
    content_type = file.content_type or "image/jpeg"

    # Database BLOB storage for Vercel / serverless / cloud deployment
    if settings.STORAGE_BACKEND in ("database", "db"):
        from backend.app.models import UploadedImage
        from backend.app.database import SessionLocal

        session = db if db is not None else SessionLocal()
        should_close = (db is None)
        try:
            new_img = UploadedImage(
                filename=unique_filename,
                content_type=content_type,
                image_data=content,
            )
            session.add(new_img)
            session.commit()
            logger.info(f"File uploaded to database BLOB: {unique_filename} ({len(content)} bytes)")
        finally:
            if should_close:
                session.close()

        return f"/api/images/{unique_filename}"

    # Default: Local disk storage
    try:
        os.makedirs(LOCAL_UPLOADS_DIR, exist_ok=True)
        destination_path = os.path.join(LOCAL_UPLOADS_DIR, unique_filename)
        with open(destination_path, "wb") as f:
            f.write(content)
        logger.info(f"File uploaded successfully to disk: {unique_filename} ({len(content)} bytes)")
        return f"/uploads/{unique_filename}"
    except OSError as err:
        # Fallback to database BLOB if local disk is read-only (e.g. on Vercel)
        logger.warning(f"Local disk write failed ({err}). Falling back to database BLOB storage.")
        from backend.app.models import UploadedImage
        from backend.app.database import SessionLocal

        session = db if db is not None else SessionLocal()
        should_close = (db is None)
        try:
            new_img = UploadedImage(
                filename=unique_filename,
                content_type=content_type,
                image_data=content,
            )
            session.add(new_img)
            session.commit()
        finally:
            if should_close:
                session.close()

        return f"/api/images/{unique_filename}"
