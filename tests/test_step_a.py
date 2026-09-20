import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ai_service import generate_suggestions
from backend.app.database import SessionLocal
from backend.app.models import User, IssueSupporter

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
def student4_token():
    res = client.post("/api/auth/login", json={"email": "student4@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_ai_suggestion_rule_engine():
    """Verify rule-based suggestion engine accurately maps sample keywords."""
    res_proj = generate_suggestions("The projector in seminar hall is broken and not working.")
    assert res_proj["category"] == "Equipment"
    assert res_proj["priority"] == "High"
    assert res_proj["source"] == "rules"
    assert 0.3 <= res_proj["confidence"] <= 0.95

    res_tap = generate_suggestions("Continuous leak and leaking tap in washroom with water overflowing.")
    assert res_tap["category"] == "Plumbing"
    assert res_tap["priority"] == "High"
    assert res_tap["source"] == "rules"

    res_spark = generate_suggestions("Danger! Sparking wire and electrical shock risk from switchboard.")
    assert res_spark["category"] == "Electrical"
    assert res_spark["priority"] == "Critical"
    assert res_spark["source"] == "rules"

    res_floor = generate_suggestions("Dirty floor and trash spilled near hallway corridor.")
    assert res_floor["category"] == "Cleaning"
    assert res_floor["priority"] in ["Low", "Medium"]
    assert res_floor["source"] == "rules"


def test_ai_suggest_api_endpoint(student1_token):
    """Verify POST /api/ai/suggest returns structured AI inference with rules source."""
    payload = {
        "description": "Projector not working in Room 204. Power LED blinks red.",
        "block": "Block A",
        "room": "Room 204",
    }
    res = client.post("/api/ai/suggest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "Equipment"
    assert data["priority"] == "High"
    assert "projector" in data["summary"].lower()
    assert data["source"] == "rules"
    assert data["confidence"] > 0.5


def test_check_duplicates_detects_seeded_near_duplicate(student1_token):
    """Verify duplicate detection endpoint flags seeded Room 204 projector issue."""
    payload = {
        "category": "Equipment",
        "block": "Block A",
        "room": "Room 204",
        "description": "Projector not working in Room 204 with red flashing light.",
    }
    res = client.post(
        "/api/issues/check-duplicates",
        json=payload,
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["has_duplicates"] is True
    assert len(data["duplicates"]) >= 1

    top_match = data["duplicates"][0]
    assert top_match["score"] >= 0.55
    assert "projector" in top_match["title"].lower()
    assert top_match["room"] == "Room 204"
    assert top_match["status"] in ["Open", "Assigned", "In Progress"]


def test_support_issue_lifecycle(student1_token, student4_token):
    """
    Verify issue support rules:
    - User cannot support own issue
    - Another user can support, incrementing count
    - User cannot support the same issue twice
    - User cannot support a resolved issue
    """
    # 0. Ensure student4 has not yet supported Issue 1 (idempotent cleanup)
    db = SessionLocal()
    s4_user = db.query(User).filter(User.email == "student4@fixflow.demo").first()
    if s4_user:
        db.query(IssueSupporter).filter(IssueSupporter.issue_id == 1, IssueSupporter.user_id == s4_user.user_id).delete()
        db.commit()
    db.close()

    # Issue 1 was reported by student1 (idx 0 -> student1)
    # 1. Student1 cannot support own issue
    res_own = client.post(
        "/api/issues/1/support",
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res_own.status_code == 400
    assert "own" in res_own.json()["detail"].lower()

    # 2. Student4 supports Issue 1 (has not supported yet)
    res_supp = client.post(
        "/api/issues/1/support",
        headers={"Authorization": f"Bearer {student4_token}"},
    )
    assert res_supp.status_code == 200
    data = res_supp.json()
    assert data["issue_id"] == 1
    assert data["support_count"] >= 2

    # 3. Student4 tries to support Issue 1 again -> 400
    res_dup_supp = client.post(
        "/api/issues/1/support",
        headers={"Authorization": f"Bearer {student4_token}"},
    )
    assert res_dup_supp.status_code == 400
    assert "already supported" in res_dup_supp.json()["detail"].lower()

    # 4. Cannot support a resolved issue (Issue 6 in seed data is Resolved)
    res_resolved = client.post(
        "/api/issues/6/support",
        headers={"Authorization": f"Bearer {student4_token}"},
    )
    assert res_resolved.status_code == 400
    assert "resolved" in res_resolved.json()["detail"].lower()
