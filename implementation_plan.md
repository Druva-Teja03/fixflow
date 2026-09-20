# FixFlow Implementation Plan

FixFlow is an AI-assisted campus issue reporting and resolution platform for students, admins, and staff members, moving issues across the strict lifecycle: `REPORT → CLASSIFY → PRIORITIZE → ASSIGN → RESOLVE`.

---

## 10-Line Project Understanding Summary
1. **Purpose:** Centralize campus infrastructure complaints into an actionable, tracked, and measurable resolution workflow.
2. **Roles:** Students (report, track, support duplicates), Admins (triage, prioritize, assign, view analytics), and Staff (task queue, progress updates).
3. **Core Lifecycle:** Strict status transitions (`Open → Assigned → In Progress → Resolved`) with immutable `status_history` logging.
4. **AI Capabilities:** Amazon Bedrock (via Converse API) suggests category, priority (Low/Med/High/Critical), and smart summary, with a robust rule-based fallback.
5. **Key Innovation:** Duplicate Issue Detection (location + category + description scoring) lets students "Support" existing issues rather than filing duplicates.
6. **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.x + PyMySQL + JWT/bcrypt security.
7. **Frontend:** Vanilla HTML5, CSS3, and ES6 JavaScript (Chart.js via CDN for analytics; no heavy JS frameworks).
8. **Storage:** Configurable local disk (`backend/uploads/`) or private AWS S3 with pre-signed GET URLs.
9. **Zero-AWS Local Execution:** Runs completely locally with local storage and rule-based AI; switches to AWS (S3, RDS, Bedrock, EC2) via `.env`.
10. **Data Integrity:** Fully seeded MySQL database with realistic demo issues, analytics history, and duplicate test pairs.

---

## Phase Roadmap (Section 15 of README)

| Phase | Description | Deliverables | Verification Step |
|---|---|---|---|
| **Phase 1** | **Foundation** | Folder structure, `config.py`, `database.py`, `models.py`, `schema.sql`, `seed.sql`/`seed.py`, `main.py` serving static files & `/docs` | App boots and connects to MySQL; `/api/health` returns 200 OK |
| **Phase 2** | **Auth & Roles** | Register, login, `/api/auth/me`, JWT verification, role guards, frontend auth forms & redirection | Seeded accounts (student, admin, staff) login and redirect to respective dashboards |
| **Phase 3** | **Student Flow** | Multi-step report form, photo upload, `POST /api/issues`, `GET /api/issues/mine`, detail view | Student submits issue with photo and sees it in My Reports as `Open` |
| **Phase 4** | **Admin & Staff Flow** | Live dashboard stat cards, issue filters, assign to staff, status updates (`status_history`), staff task queue | Moving `Open → Assigned → In Progress → Resolved` updates timeline in real-time |
| **Phase 5** | **AWS Integration** | Switchable S3 storage service with pre-signed URLs, RDS env support, EC2 deployment guide | Switching `STORAGE_BACKEND=s3` loads photo via S3 pre-signed URL |
| **Phase 6** | **AI & Duplicate Detection** | `/api/ai/suggest` (Bedrock + keyword fallback), duplicate detection candidate filter & scoring, "Support this issue" | "Projector broken" in Room 204 suggests Equipment/High; 2nd report triggers duplicate modal |
| **Phase 7** | **Analytics & Polish** | Analytics APIs, Chart.js visualizations (category, block, trend, hotspots, heatmap), comments, UI polish | Analytics page displays charts, heatmap, and average resolution time accurately |
| **Phase 8** | **Docs & Demo Prep** | Demo script (`docs/demo-script.md`), README verification, pytest test suite | All acceptance checklist items verified; automated tests pass |

---

## Phase 1 Execution Details

### Proposed Changes
- Create `requirements.txt` with required dependencies.
- Setup Python 3.12 virtual environment `venv/`.
- Create `.env.example` and local `.env`.
- Create `database/schema.sql` defining all 6 relational tables with indexes and foreign keys.
- Create `backend/seed.py` and `database/seed.sql` with demo users (admin, staff, students) and 20+ realistic issues.
- Setup `fixflow` database in local MySQL Server 8.0 with dedicated user `fixflow_user`.
- Create `backend/app/config.py` using `pydantic-settings`.
- Create `backend/app/database.py` with SQLAlchemy engine, `SessionLocal`, and DB connection check.
- Create `backend/app/models.py` with SQLAlchemy 2.0 ORM mappings.
- Create `backend/app/main.py` with FastAPI, CORS, static file serving, and `/api/health`.
- Create minimal placeholder `frontend/index.html` and `frontend/css/styles.css` to verify static file serving.

### Verification Plan
- Create DB and run schema + seed scripts.
- Run `uvicorn backend.app.main:app --port 8000`.
- Verify `GET http://localhost:8000/api/health` returns `{"status": "ok", "database": "connected"}`.
- Verify `http://localhost:8000/docs` loads Swagger UI.
- Verify `http://localhost:8000/` serves the frontend foundation.
