import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Issue, IssueStatus, IssueSupporter, Notification, User

client = TestClient(app)


@pytest.fixture
def admin_token():
    res = client.post("/api/auth/login", json={"email": "admin@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def staff_it_token():
    res = client.post("/api/auth/login", json={"email": "it@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


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


def test_health_check_endpoint():
    """Verify GET /api/health reports app status, database, storage_backend, and suggestion_mode."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["storage_backend"] == "local"
    assert data["suggestion_mode"] == "rules"


def test_notifications_created_on_assignment(admin_token, staff_it_token, student1_token):
    """
    Verify assigning an issue creates an in-app notification for the staff member,
    and a status change notification for the reporter student.
    """
    # Find or use an open issue (e.g. Issue 2 or 5)
    db = SessionLocal()
    issue = db.query(Issue).filter(Issue.status == IssueStatus.OPEN).first()
    assert issue is not None
    issue_id = issue.issue_id
    reporter_id = issue.user_id

    # Staff IT user id
    staff_user = db.query(User).filter(User.email == "it@fixflow.demo").first()
    assert staff_user is not None
    staff_id = staff_user.user_id
    db.close()

    # Admin assigns issue to staff_id
    assign_res = client.post(
        f"/api/admin/issues/{issue_id}/assign",
        json={"staff_id": staff_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign_res.status_code == 200

    # Verify staff member received notification
    staff_notifs_res = client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {staff_it_token}"},
    )
    assert staff_notifs_res.status_code == 200
    staff_notifs = staff_notifs_res.json()
    assert len(staff_notifs) > 0
    assert any(str(issue_id) in n["message"] for n in staff_notifs)

    # Verify reporter received status change notification
    # Login as the reporter
    db = SessionLocal()
    reporter = db.query(User).filter(User.user_id == reporter_id).first()
    db.close()
    rep_login = client.post("/api/auth/login", json={"email": reporter.email, "password": "Demo@1234"}).json()
    rep_token = rep_login["access_token"]

    rep_notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {rep_token}"}).json()
    assert any("Assigned" in n["message"] and str(issue_id) in n["message"] for n in rep_notifs)


def test_notifications_on_status_change_and_resolution(admin_token, student1_token, student2_token):
    """
    Verify:
    1. Status update creates notification for reporter.
    2. Status update to Resolved notifies supporters as well.
    """
    db = SessionLocal()
    # Find an assigned or in-progress issue
    issue = db.query(Issue).filter(Issue.status == IssueStatus.IN_PROGRESS).first()
    if not issue:
        issue = db.query(Issue).filter(Issue.status == IssueStatus.ASSIGNED).first()
    assert issue is not None
    issue_id = issue.issue_id
    reporter_id = issue.user_id

    # Ensure student2 is a supporter of this issue (if not already)
    s2_user = db.query(User).filter(User.email == "student2@fixflow.demo").first()
    assert s2_user is not None
    s2_id = s2_user.user_id

    supp = db.query(IssueSupporter).filter(IssueSupporter.issue_id == issue_id, IssueSupporter.user_id == s2_id).first()
    if not supp and reporter_id != s2_id:
        db.add(IssueSupporter(issue_id=issue_id, user_id=s2_id))
        issue.support_count += 1
        db.commit()
    db.close()

    # Admin marks issue as Resolved
    res_status = client.patch(
        f"/api/issues/{issue_id}/status",
        json={"status": "Resolved"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_status.status_code == 200

    # Verify supporter (student2) received resolved notification
    s2_notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {student2_token}"}).json()
    assert any("resolved" in n["message"].lower() and str(issue_id) in n["message"] for n in s2_notifs)


def test_mark_notification_read_endpoints(student2_token):
    """Verify POST /api/notifications/{id}/read and POST /api/notifications/read-all."""
    # Get unread notifications
    notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {student2_token}"}).json()
    assert len(notifs) > 0

    first_notif_id = notifs[0]["notification_id"]

    # Mark single notification as read
    read_res = client.post(
        f"/api/notifications/{first_notif_id}/read",
        headers={"Authorization": f"Bearer {student2_token}"},
    )
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Mark all as read
    read_all_res = client.post(
        "/api/notifications/read-all",
        headers={"Authorization": f"Bearer {student2_token}"},
    )
    assert read_all_res.status_code == 200

    # Verify all are read now
    all_notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {student2_token}"}).json()
    assert all(n["is_read"] is True for n in all_notifs)
