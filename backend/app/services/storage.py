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

os.makedirs(LOCAL_UPLOADS_DIR, exist_ok=True)


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


async def save_uploaded_file(file: Optional[UploadFile]) -> Optional[str]:
    """
    Validates, renames to a UUID, and saves an uploaded photo.
    Returns the public URL string (e.g. '/uploads/uuid.jpg') or None if no file was uploaded.
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

    # Storage backend selection
    if settings.STORAGE_BACKEND == "s3":
        # S3 integration will be plugged in Phase 5
        logger.info("Storage backend set to S3. (Phase 5 will upload to S3). Saving locally for now.")
    
    # Local disk storage
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    destination_path = os.path.join(LOCAL_UPLOADS_DIR, unique_filename)

    with open(destination_path, "wb") as f:
        f.write(content)

    logger.info(f"File uploaded successfully: {unique_filename} ({len(content)} bytes)")
    return f"/uploads/{unique_filename}"
