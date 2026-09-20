import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Issue, StatusHistory

client = TestClient(app)


@pytest.fixture
def student1_token():
    res = client.post("/api/auth/login", json={"email": "student1@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def student2_token():
    res = client.post("/api/auth/login", json={"email": "student2@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def admin_token():
    res = client.post("/api/auth/login", json={"email": "admin@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_get_meta_options():
    """Verify meta options endpoint returns valid dropdown choices."""
    res = client.get("/api/meta/options")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data and "Equipment" in data["categories"]
    assert "blocks" in data and "Block A" in data["blocks"]
    assert "priorities" in data and "High" in data["priorities"]
    assert "statuses" in data and "Open" in data["statuses"]


def test_create_issue_writes_status_history(student1_token):
    """Verify creating an issue sets status to Open, support_count=1, and logs first status_history."""
    payload = {
        "title": "Broken Lab Bench Stool",
        "description": "The wooden stool in Physics Lab 2 has a broken leg and cannot be used safely.",
        "category": "Furniture",
        "block": "Block B",
        "building": "Science Block",
        "room": "Physics Lab 2",
        "priority": "Medium",
    }
    # Optional image test: 1x1 valid PNG bytes
    fake_png = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    files = {"image": ("test_photo.png", fake_png, "image/png")}

    res = client.post(
        "/api/issues",
        data=payload,
        files=files,
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res.status_code == 201, res.text
    created = res.json()
    assert created["status"] == "Open"
    assert created["support_count"] == 1
    assert created["image_url"] is not None
    assert created["image_url"].startswith("/uploads/")

    issue_id = created["issue_id"]

    # Verify status_history row in DB
    db = SessionLocal()
    try:
        history = db.query(StatusHistory).filter(StatusHistory.issue_id == issue_id).all()
        assert len(history) >= 1
        assert history[0].old_status is None
        assert history[0].new_status == "Open"
    finally:
        db.close()


def test_student_cannot_read_another_student_issue(student1_token, student2_token, admin_token):
    """Verify student B receives 403 Forbidden when attempting to view Student A's issue."""
    # Student 1 creates an issue
    payload = {
        "title": "Private Issue for Student 1",
        "description": "Only student 1 and campus authorities should be able to view this.",
        "category": "Other",
        "block": "Block C",
        "priority": "Low",
    }
    res = client.post(
        "/api/issues",
        data=payload,
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res.status_code == 201
    issue_id = res.json()["issue_id"]

    # Student 1 can view their own issue
    res_owner = client.get(
        f"/api/issues/{issue_id}",
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res_owner.status_code == 200

    # Student 2 receives 403 Forbidden
    res_other = client.get(
        f"/api/issues/{issue_id}",
        headers={"Authorization": f"Bearer {student2_token}"},
    )
    assert res_other.status_code == 403
    detail = res_other.json()["detail"].lower()
    assert "forbidden" in detail or "not authorized" in detail

    # Admin can view the issue
    res_admin = client.get(
        f"/api/issues/{issue_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200


def test_upload_validation_rejects_bad_file_type(student1_token):
    """Verify upload rejects non-image formats (e.g., text/plain, application/pdf)."""
    payload = {
        "title": "Invalid File Test",
        "description": "Attempting to upload a text file instead of an image.",
        "category": "Other",
        "block": "Block A",
        "priority": "Low",
    }
    bad_file = io.BytesIO(b"Fake executable or script content")
    files = {"image": ("malicious.exe", bad_file, "application/octet-stream")}

    res = client.post(
        "/api/issues",
        data=payload,
        files=files,
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res.status_code == 400
    assert "Invalid image format" in res.json()["detail"]


def test_upload_validation_rejects_oversized_file(student1_token):
    """Verify upload rejects files larger than 5 MB."""
    payload = {
        "title": "Oversized File Test",
        "description": "Attempting to upload an oversized image.",
        "category": "Other",
        "block": "Block A",
        "priority": "Low",
    }
    # 5.2 MB payload
    oversized = io.BytesIO(b"0" * (5 * 1024 * 1024 + 200 * 1024))
    files = {"image": ("huge_photo.jpg", oversized, "image/jpeg")}

    res = client.post(
        "/api/issues",
        data=payload,
        files=files,
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res.status_code == 400
    assert "exceeds 5 MB limit" in res.json()["detail"]


def test_comments_and_permission_enforcement(student1_token, student2_token):
    """Verify adding/retrieving comments and enforcing that another student cannot comment."""
    # Student 1 creates an issue
    payload = {
        "title": "Comment Testing Issue",
        "description": "Testing discussion on this reported item.",
        "category": "Cleaning",
        "block": "Block D",
        "priority": "Low",
    }
    res = client.post("/api/issues", data=payload, headers={"Authorization": f"Bearer {student1_token}"})
    assert res.status_code == 201
    issue_id = res.json()["issue_id"]

    # Student 1 posts a comment
    res_comment = client.post(
        f"/api/issues/{issue_id}/comments",
        json={"comment": "I have also noticed this in the morning."},
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res_comment.status_code == 201
    assert res_comment.json()["comment"] == "I have also noticed this in the morning."

    # Student 1 reads comments
    res_get = client.get(
        f"/api/issues/{issue_id}/comments",
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res_get.status_code == 200
    assert len(res_get.json()) == 1

    # Student 2 tries to comment on Student 1's issue -> 403 Forbidden
    res_bad_comment = client.post(
        f"/api/issues/{issue_id}/comments",
        json={"comment": "Unauthorized comment attempt."},
        headers={"Authorization": f"Bearer {student2_token}"},
    )
    assert res_bad_comment.status_code == 403
