import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

ANALYTICS_ENDPOINTS = [
    "/api/analytics/summary",
    "/api/analytics/by-category",
    "/api/analytics/by-block",
    "/api/analytics/by-status",
    "/api/analytics/trend?days=30",
    "/api/analytics/hotspots",
    "/api/analytics/heatmap",
    "/api/analytics/resolution-time",
]


@pytest.fixture
def admin_token():
    res = client.post("/api/auth/login", json={"email": "admin@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def student_token():
    res = client.post("/api/auth/login", json={"email": "student1@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


@pytest.fixture
def staff_token():
    res = client.post("/api/auth/login", json={"email": "electric@fixflow.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_admin_can_access_all_analytics(admin_token):
    """Verify administrator has full access to all 8 analytics endpoints."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    for endpoint in ANALYTICS_ENDPOINTS:
        res = client.get(endpoint, headers=headers)
        assert res.status_code == 200, f"Endpoint {endpoint} failed: {res.text}"

    # Verify structured content of specific endpoints
    cat_res = client.get("/api/analytics/by-category", headers=headers)
    cat_data = cat_res.json()
    assert len(cat_data) > 0
    assert any(c["category"] == "Equipment" for c in cat_data)

    trend_res = client.get("/api/analytics/trend?days=30", headers=headers)
    trend_data = trend_res.json()
    assert len(trend_data) == 30

    heatmap_res = client.get("/api/analytics/heatmap", headers=headers)
    heatmap_data = heatmap_res.json()
    assert "Block A" in heatmap_data["blocks"]
    assert "Equipment" in heatmap_data["categories"]
    assert heatmap_data["max_count"] >= 1

    res_time = client.get("/api/analytics/resolution-time", headers=headers).json()
    assert res_time["resolved_count"] > 0
    assert res_time["average_hours"] > 0


def test_student_rejected_from_analytics(student_token):
    """Verify non-admin students are rejected with 403 Forbidden on all analytics endpoints."""
    headers = {"Authorization": f"Bearer {student_token}"}
    for endpoint in ANALYTICS_ENDPOINTS:
        res = client.get(endpoint, headers=headers)
        assert res.status_code == 403, f"Endpoint {endpoint} did not return 403: {res.status_code}"


def test_staff_rejected_from_analytics(staff_token):
    """Verify technicians/staff are rejected with 403 Forbidden on all analytics endpoints."""
    headers = {"Authorization": f"Bearer {staff_token}"}
    for endpoint in ANALYTICS_ENDPOINTS:
        res = client.get(endpoint, headers=headers)
        assert res.status_code == 403, f"Endpoint {endpoint} did not return 403: {res.status_code}"


def test_unauthenticated_rejected_from_analytics():
    """Verify unauthenticated requests are rejected with 401 Unauthorized."""
    for endpoint in ANALYTICS_ENDPOINTS:
        res = client.get(endpoint)
        assert res.status_code == 401, f"Endpoint {endpoint} did not return 401: {res.status_code}"
