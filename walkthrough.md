# Phase 1 — Foundation Walkthrough

## Summary of Completed Work
Phase 1 of **FixFlow** has been built and verified against a live local MySQL database. The application boots cleanly, connects to MySQL, and serves both interactive Swagger documentation (`/docs`) and the initial frontend UI.

---

## What Was Built

1. **Virtual Environment & Dependencies:**
   - Initialized Python 3.12 virtual environment (`venv/`).
   - Installed FastAPI, Uvicorn, SQLAlchemy 2.x, PyMySQL, Cryptography, Pydantic-Settings, Passlib with Bcrypt, Boto3, and Pytest.
   - Resolved Passlib 1.7.4 compatibility with Bcrypt 4.1+ cleanly.

2. **Configuration & Security Layer:**
   - [`backend/app/config.py`](file:///e:/AXON%20FixFlow/backend/app/config.py): Environment settings via `pydantic-settings` supporting switchable local and AWS modes. Credentials with special characters like `@` are automatically URL-encoded for PyMySQL.
   - [`backend/app/security.py`](file:///e:/AXON%20FixFlow/backend/app/security.py): Bcrypt password hashing context and JWT access token creation/decoding functions with configurable expiry.
   - [`.env.example`](file:///e:/AXON%20FixFlow/.env.example) and [`.env`](file:///e:/AXON%20FixFlow/.env): Clean configuration with no hardcoded production secrets.

3. **Relational Database Design (MySQL 8):**
   - [`database/schema.sql`](file:///e:/AXON%20FixFlow/database/schema.sql): Complete DDL for all 6 core tables:
     - `users` (students, admin, staff)
     - `issues` (location, category, priority, status, AI fields, support count)
     - `assignments` (staff allocations by admin)
     - `comments` (timeline comments)
     - `issue_supporters` (duplicate upvoting)
     - `status_history` (audit trail of state transitions)
   - Created MySQL database `fixflow` and dedicated user `fixflow_user` with full privileges.

4. **Seeding & Realistic Data:**
   - [`backend/seed.py`](file:///e:/AXON%20FixFlow/backend/seed.py): Python seed script populating 1 Admin, 3 Staff members (Electrical, IT, Plumbing), 5 Students, and 25 realistic issues spread across 4 campus blocks over the past 30 days.
   - Included a verified near-duplicate pair in Room 204 (*"Projector not working in Room 204"* and *"Broken projector / display not turning on"*) ready for Phase 6 duplicate detection.
   - [`database/seed.sql`](file:///e:/AXON%20FixFlow/database/seed.sql): Generated pure SQL seed dump for direct CLI imports.

5. **ORM Models & Session Management:**
   - [`backend/app/database.py`](file:///e:/AXON%20FixFlow/backend/app/database.py): SQLAlchemy engine with `pool_pre_ping=True`, session lifecycle dependency (`get_db`), and connection ping.
   - [`backend/app/models.py`](file:///e:/AXON%20FixFlow/backend/app/models.py): Declarative ORM models with enum bindings and foreign key relationships.

6. **FastAPI Application & Frontend Static Serving:**
   - [`backend/app/main.py`](file:///e:/AXON%20FixFlow/backend/app/main.py): FastAPI app with CORS middleware, lifespan database health validation, `/api/health` endpoint, `/uploads` photo directory mount, and static frontend mount at root `/`.
   - [`frontend/index.html`](file:///e:/AXON%20FixFlow/frontend/index.html): Landing and login interface with one-click demo credentials for quick evaluation.
   - [`frontend/css/styles.css`](file:///e:/AXON%20FixFlow/frontend/css/styles.css): Design system with CSS tokens, status/priority color badges, card layouts, and responsive utilities.
   - [`frontend/js/api.js`](file:///e:/AXON%20FixFlow/frontend/js/api.js) & [`frontend/js/auth.js`](file:///e:/AXON%20FixFlow/frontend/js/auth.js): Fetch client and role-based redirect guards.

---

## Verification Results

| Check | Target | Expected | Result |
|---|---|---|---|
| **App Startup** | `uvicorn backend.app.main:app` | Process boots without errors | **PASS** |
| **Database Connection** | `/api/health` | `{"database": "connected"}` | **PASS** |
| **API Docs** | `http://127.0.0.1:8000/docs` | HTTP 200 (Swagger UI) | **PASS** |
| **Frontend Serving** | `http://127.0.0.1:8000/` | HTTP 200 (`index.html`) | **PASS** |
| **Database Seeding** | MySQL `fixflow` tables | 9 users, 25 issues, 16 assignments, 9 comments | **PASS** |

Live `/api/health` response:
```json
{
  "status": "ok",
  "app_env": "development",
  "database": "connected",
  "storage_backend": "local",
  "ai_enabled": true
}
```

---

## How to Test Yourself

1. **Verify Backend & Health Check:**
   Open your browser or run:
   ```bash
   curl http://127.0.0.1:8000/api/health
   ```
   You will receive `{"status":"ok","database":"connected",...}`.

2. **Explore API Documentation:**
   Navigate to:
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   You will see the interactive Swagger UI.

3. **View Landing Page:**
   Navigate to:
   [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   You will see the FixFlow landing page with one-click demo logins.

---

# Phase 4 — Admin & Staff Flow (MVP Core) Walkthrough

## Summary of Completed Work
Phase 4 of **FixFlow** has been built and verified. Administrators now have a real-time operations dashboard with live metric cards, multi-filter and searchable ticket listings, incident triage (priority and category editing), and smart technician dispatch. Assigned staff members have an interactive task queue with quick status progression buttons. The strict issue lifecycle (`Open → Assigned → In Progress → Resolved`) is enforced on the backend with audit history tracking.

---

## What Was Built

1. **Backend Endpoints & Business Logic:**
   - Mounted `admin.router`, `staff.router`, and `analytics.router` in [`backend/app/main.py`](file:///e:/AXON%20FixFlow/backend/app/main.py).
   - **`GET /api/admin/issues`**: Admin-only ticket listing with filters (`status`, `category`, `block`, `priority`, search query `q`), sorting (`newest`, `priority` Critical-first, `support_count`), and pagination (`page`, `page_size`).
   - **`PATCH /api/admin/issues/{id}`**: Admin-only triage endpoint to edit priority and category.
   - **`POST /api/admin/issues/{id}/assign`**: Admin-only assignment endpoint that creates an `assignments` row, advances status to `Assigned`, writes `status_history`, supports reassignment, and triggers `notify_assignment`.
   - **`PATCH /api/issues/{id}/status`**: Lifecycle transition endpoint enforcing Section 5 strict forward rules (`Open → Assigned → In Progress → Resolved`). Admin may jump directly to `Resolved`, and only Admin may reopen `Resolved → Open`. Sets/clears `resolved_at` and logs `status_history`.
   - **`GET /api/meta/staff`**: Admin-only listing of staff members with department (`team`).
   - **`GET /api/staff/tasks`**: Staff-only queue of issues currently assigned to the logged-in staff member.
   - **`GET /api/analytics/summary`**: High-level metric counts for dashboard metric cards.

2. **Frontend Operations UI:**
   - [`frontend/admin/dashboard.html`](file:///e:/AXON%20FixFlow/frontend/admin/dashboard.html): 5 live stat cards, filter bar, search box, sort selector, and table with row click to issue details.
   - [`frontend/admin/issue.html`](file:///e:/AXON%20FixFlow/frontend/admin/issue.html): Full incident details, evidence photo preview, inline triage controls, smart technician assignment with recommended team highlighting, status progression buttons, 4-step stepper, audit log, and comments section.
   - [`frontend/staff/tasks.html`](file:///e:/AXON%20FixFlow/frontend/staff/tasks.html): Assigned maintenance task queue with quick status progression buttons.
   - [`frontend/js/admin.js`](file:///e:/AXON%20FixFlow/frontend/js/admin.js): Modular vanilla JS controller.
   - [`frontend/student/issue.html`](file:///e:/AXON%20FixFlow/frontend/student/issue.html) & [`frontend/student/my-reports.html`](file:///e:/AXON%20FixFlow/frontend/student/my-reports.html): Updated with assigned technician details and live status updates.

3. **Automated Verification:**
   - [`tests/test_phase4.py`](file:///e:/AXON%20FixFlow/tests/test_phase4.py): 8 automated pytest tests covering authorization guards, assignment records, status transition rules, and task queues. All 14 tests across the project pass.

