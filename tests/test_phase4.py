import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, Issue, Assignment, StatusHistory, IssueStatus

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


@pytest.fixture
def staff_electric_token():
    res = client.post("/api/auth/login", json={"email": "electric@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def staff_it_token():
    res = client.post("/api/auth/login", json={"email": "it@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def sample_issue(student1_token):
    """Create a fresh Open issue for testing."""
    payload = {
        "title": "Sparking Wall Outlet in Lab 3",
        "description": "Loose sparking socket behind desktop 12 in Electrical Engineering Lab 3.",
        "category": "Electrical",
        "block": "Block A",
        "building": "Main Wing",
        "room": "EE Lab 3",
        "priority": "Critical",
    }
    res = client.post(
        "/api/issues",
        data=payload,
        headers={"Authorization": f"Bearer {student1_token}"},
    )
    assert res.status_code == 201
    return res.json()


def test_student_forbidden_on_admin_endpoints(student1_token):
    """Verify that a student user receives 403 Forbidden on all admin endpoints."""
    headers = {"Authorization": f"Bearer {student1_token}"}

    # 1. GET /api/admin/issues
    res = client.get("/api/admin/issues", headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # 2. PATCH /api/admin/issues/1
    res = client.patch("/api/admin/issues/1", json={"priority": "High"}, headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # 3. POST /api/admin/issues/1/assign
    res = client.post("/api/admin/issues/1/assign", json={"staff_id": 2}, headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # 4. GET /api/meta/staff
    res = client.get("/api/meta/staff", headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    # 5. GET /api/analytics/summary
    res = client.get("/api/analytics/summary", headers=headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}"


def test_analytics_summary_and_staff_meta(admin_token):
    """Verify admin can fetch analytics summary and staff list."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Summary
    res = client.get("/api/analytics/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "open" in data
    assert "assigned" in data
    assert "in_progress" in data
    assert "resolved" in data
    assert "critical" in data

    # Staff list
    res = client.get("/api/meta/staff", headers=headers)
    assert res.status_code == 200
    staff_list = res.json()
    assert isinstance(staff_list, list)
    assert len(staff_list) >= 1
    # Confirm staff attributes
    first_staff = staff_list[0]
    assert "user_id" in first_staff
    assert "name" in first_staff
    assert "role" in first_staff
    assert first_staff["role"] == "staff"


def test_admin_list_and_filter_issues(admin_token, sample_issue):
    """Verify admin can list issues with filters, search, and sorting."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Search with q
    res = client.get("/api/admin/issues?q=Sparking", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    items = data["items"]
    assert any(i["issue_id"] == sample_issue["issue_id"] for i in items)

    # Filter by category and priority
    res = client.get("/api/admin/issues?category=Electrical&priority=Critical", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1

    # Sort by priority
    res = client.get("/api/admin/issues?sort_by=priority", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) >= 1
    # First item should be Critical if critical exists
    if any(i["priority"] == "Critical" for i in data["items"]):
        assert data["items"][0]["priority"] == "Critical"


def test_admin_patch_priority_and_category(admin_token, sample_issue):
    """Verify admin can edit priority and category via PATCH /api/admin/issues/{id}."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    issue_id = sample_issue["issue_id"]

    res = client.patch(
        f"/api/admin/issues/{issue_id}",
        json={"priority": "High", "category": "Equipment"},
        headers=headers,
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["priority"] == "High"
    assert updated["category"] == "Equipment"


def test_assignment_creates_records_and_updates_status(admin_token, staff_electric_token, sample_issue):
    """
    Verify assigning an issue creates an assignments row,
    moves status to Assigned, writes status_history,
    and handles reassignment while preserving history.
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    issue_id = sample_issue["issue_id"]

    # 1. Fetch staff user ID for electric@fixflow.demo
    staff_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {staff_electric_token}"}).json()
    electric_staff_id = staff_me["user_id"]

    # 2. Assign to Electrician
    res = client.post(
        f"/api/admin/issues/{issue_id}/assign",
        json={"staff_id": electric_staff_id},
        headers=admin_headers,
    )
    assert res.status_code == 200, res.text
    assigned_item = res.json()
    assert assigned_item["status"] == "Assigned"
    assert assigned_item["assigned_staff_id"] == electric_staff_id
    assert assigned_item["assigned_staff_name"] == staff_me["name"]

    # 3. Verify DB records
    db = SessionLocal()
    try:
        assignments = db.query(Assignment).filter(Assignment.issue_id == issue_id).all()
        assert len(assignments) == 1
        assert assignments[0].staff_id == electric_staff_id

        history = (
            db.query(StatusHistory)
            .filter(StatusHistory.issue_id == issue_id)
            .order_by(StatusHistory.history_id.asc())
            .all()
        )
        # Should have initial Open history + Assigned history
        assert len(history) >= 2
        assert history[-1].old_status == "Open"
        assert history[-1].new_status == "Assigned"
    finally:
        db.close()

    # 4. Reassign to IT staff and verify history is preserved
    staff_it_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {staff_electric_token}"}).json()
    it_staff = db.query(User).filter(User.email == "it@fixflow.demo").first()
    it_staff_id = it_staff.user_id

    res_reassign = client.post(
        f"/api/admin/issues/{issue_id}/assign",
        json={"staff_id": it_staff_id},
        headers=admin_headers,
    )
    assert res_reassign.status_code == 200
    assert res_reassign.json()["assigned_staff_id"] == it_staff_id

    # Verify assignments table now has 2 rows
    db = SessionLocal()
    try:
        assignments = db.query(Assignment).filter(Assignment.issue_id == issue_id).all()
        assert len(assignments) == 2
    finally:
        db.close()


def test_status_transition_authorization_and_validation(
    admin_token,
    student1_token,
    staff_electric_token,
    staff_it_token,
    sample_issue,
):
    """
    Comprehensive verification of Section 5 status transitions and authorization:
    - Student gets 403
    - Unassigned staff gets 403
    - Assigned staff can move Assigned -> In Progress -> Resolved
    - Assigned staff CANNOT reopen Resolved -> Open (403)
    - Admin CAN reopen Resolved -> Open (200)
    - Reopening clears resolved_at
    - Invalid transitions return 400
    """
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student1_token}"}
    electric_headers = {"Authorization": f"Bearer {staff_electric_token}"}
    it_headers = {"Authorization": f"Bearer {staff_it_token}"}

    issue_id = sample_issue["issue_id"]

    # Assign to electric staff
    electric_user = client.get("/api/auth/me", headers=electric_headers).json()
    assign_res = client.post(
        f"/api/admin/issues/{issue_id}/assign",
        json={"staff_id": electric_user["user_id"]},
        headers=admin_headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "Assigned"

    # 1. Student attempting status update -> 403
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "In Progress"}, headers=student_headers)
    assert res.status_code == 403

    # 2. Unassigned staff (IT) attempting status update -> 403
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "In Progress"}, headers=it_headers)
    assert res.status_code == 403

    # 3. Invalid transition: Assigned -> Open -> 400
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Open"}, headers=electric_headers)
    assert res.status_code == 400

    # 4. Same status: Assigned -> Assigned -> 400
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Assigned"}, headers=electric_headers)
    assert res.status_code == 400

    # 5. Assigned staff moves Assigned -> In Progress -> 200
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "In Progress"}, headers=electric_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["status"] == "In Progress"
    assert detail["resolved_at"] is None

    # 6. Invalid backward transition: In Progress -> Assigned -> 400
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Assigned"}, headers=electric_headers)
    assert res.status_code == 400

    # 7. Assigned staff moves In Progress -> Resolved -> 200 and sets resolved_at
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Resolved"}, headers=electric_headers)
    assert res.status_code == 200
    resolved_detail = res.json()
    assert resolved_detail["status"] == "Resolved"
    assert resolved_detail["resolved_at"] is not None

    # 8. Assigned staff attempts to reopen Resolved -> Open -> 403 (Admin only)
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Open"}, headers=electric_headers)
    assert res.status_code == 403

    # 9. Admin reopens Resolved -> Open -> 200 and clears resolved_at
    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Open"}, headers=admin_headers)
    assert res.status_code == 200
    reopened_detail = res.json()
    assert reopened_detail["status"] == "Open"
    assert reopened_detail["resolved_at"] is None


def test_admin_direct_jump_to_resolved(admin_token, sample_issue):
    """Verify admin can jump directly from Open to Resolved."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    issue_id = sample_issue["issue_id"]

    res = client.patch(f"/api/issues/{issue_id}/status", json={"status": "Resolved"}, headers=admin_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["status"] == "Resolved"
    assert detail["resolved_at"] is not None


def test_staff_tasks_endpoint(admin_token, staff_it_token, sample_issue):
    """Verify GET /api/staff/tasks returns issues assigned to the logged-in staff member."""
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    it_headers = {"Authorization": f"Bearer {staff_it_token}"}

    it_user = client.get("/api/auth/me", headers=it_headers).json()
    issue_id = sample_issue["issue_id"]

    # Assign sample issue to IT staff
    assign_res = client.post(
        f"/api/admin/issues/{issue_id}/assign",
        json={"staff_id": it_user["user_id"]},
        headers=admin_headers,
    )
    assert assign_res.status_code == 200

    # IT staff checks tasks
    res = client.get("/api/staff/tasks", headers=it_headers)
    assert res.status_code == 200
    tasks = res.json()
    assert isinstance(tasks, list)
    matching = [t for t in tasks if t["issue_id"] == issue_id]
    assert len(matching) == 1
    assert matching[0]["title"] == sample_issue["title"]
    assert matching[0]["status"] == "Assigned"
