import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models import UploadedImage, Issue

client = TestClient(app)


@pytest.fixture
def student1_token():
    res = client.post(
        "/api/auth/login",
        json={"email": "student1@fixflow.demo", "password": "Demo@1234"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_public_static_files_served():
    """Verify that static files from public/ are served at expected root URLs."""
    # Root index.html
    res = client.get("/")
    assert res.status_code == 200
    assert "FixFlow" in res.text

    # CSS file
    res = client.get("/css/styles.css")
    assert res.status_code == 200
    assert "--primary" in res.text

    # Student dashboard HTML
    res = client.get("/student/dashboard.html")
    assert res.status_code == 200
    assert "FixFlow" in res.text


def test_database_blob_image_storage(student1_token):
    """
    Verify that when STORAGE_BACKEND='database', uploaded images are stored
    as BLOBs in the MySQL `uploaded_images` table and served via endpoints.
    """
    original_backend = settings.STORAGE_BACKEND
    settings.STORAGE_BACKEND = "database"

    try:
        payload = {
            "title": "Broken window in Room 102 (Vercel test)",
            "description": "Glass window pane is cracked and loose after storm.",
            "category": "Doors/Windows",
            "block": "Block A",
            "building": "Main Block",
            "room": "Room 102",
            "priority": "Medium",
        }
        test_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        files = {"image": ("window_crack.png", io.BytesIO(test_bytes), "image/png")}

        res = client.post(
            "/api/issues",
            data=payload,
            files=files,
            headers={"Authorization": f"Bearer {student1_token}"},
        )
        assert res.status_code == 201, res.text
        data = res.json()
        assert data["image_url"] is not None
        assert data["image_url"].startswith("/api/images/")
        image_url = data["image_url"]
        filename = image_url.split("/")[-1]

        # 1. Verify endpoint /api/images/{filename} returns binary content
        img_res = client.get(image_url)
        assert img_res.status_code == 200
        assert img_res.content == test_bytes
        assert "image/png" in img_res.headers.get("content-type", "")

        # 2. Verify dual-serving via /uploads/{filename} also returns the binary content
        uploads_res = client.get(f"/uploads/{filename}")
        assert uploads_res.status_code == 200
        assert uploads_res.content == test_bytes

        # 3. Verify DB record in uploaded_images table
        db = SessionLocal()
        try:
            record = db.query(UploadedImage).filter(UploadedImage.filename == filename).first()
            assert record is not None
            assert record.image_data == test_bytes
            assert record.content_type == "image/png"
        finally:
            db.close()

    finally:
        settings.STORAGE_BACKEND = original_backend


def test_db_ssl_setting():
    """Verify that DB_SSL configuration property is present and defaults to False."""
    assert hasattr(settings, "DB_SSL")
    assert settings.DB_SSL is False


def test_empty_environment_variables_fallback_to_defaults(monkeypatch):
    """Verify that empty string env vars are treated as not set and use defaults."""
    from backend.app.config import Settings

    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_HOURS", "")
    monkeypatch.setenv("DB_PORT", "")
    monkeypatch.setenv("AI_ENABLED", "")
    monkeypatch.setenv("NOTIFICATIONS_ENABLED", "")

    test_settings = Settings()
    assert test_settings.ACCESS_TOKEN_EXPIRE_HOURS == 12
    assert test_settings.DB_PORT == 3306
    assert test_settings.AI_ENABLED is True
    assert test_settings.NOTIFICATIONS_ENABLED is False

