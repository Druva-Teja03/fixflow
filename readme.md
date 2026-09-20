# FixFlow — Smart Campus Issue Reporting & Resolution Platform

> **One-line idea:** FixFlow lets students report campus infrastructure problems in seconds and helps management track, prioritize, assign, and resolve them — with smart suggestion assistance, duplicate detection, and real-time operations analytics.

**Workflow:** `REPORT → CLASSIFY → PRIORITIZE → ASSIGN → RESOLVE`

---

## Zero-Cloud Architecture & Operating Mode

> [!NOTE]
> **Zero-AWS Local Execution:** FixFlow runs **completely locally** without any external cloud dependencies.
> - **Photos / Evidence:** Stored directly on local disk (`STORAGE_BACKEND=local`, directory `backend/uploads/` served at `/uploads/`).
> - **Smart Suggestions:** Powered by a deterministic, high-accuracy **Rule-Based NLP Engine** (keyword maps, confidence scoring, smart summary extraction).
> - **Database:** Local **MySQL 8** accessed via SQLAlchemy 2.x and PyMySQL.
> - **In-App Notifications:** Stored in the local relational database with real-time UI bell dropdowns.
> - **Cloud Pluggability:** Modules (`storage.py`, `ai_service.py`, `notifications.py`) use clean service interfaces so cloud providers (AWS S3, Bedrock, RDS, SES) can be plugged in as future extensions without altering core business workflows.

---

## What is Done (Completion Checklist)

- [x] **Phase 1 — Foundation:** Complete directory structure, configuration layer (`config.py`), local MySQL connection with SQLAlchemy 2.x, database schema (`schema.sql`), deterministic seed script (`backend/seed.py`), static frontend mounting, and health check.
- [x] **Phase 2 — Auth & Security:** Student registration, JWT token generation (`/api/auth/login`), `/api/auth/me`, bcrypt password hashing, role guards (`student`, `admin`, `staff`), and landing page redirect guards.
- [x] **Phase 3 — Student Flow:** Multi-step incident reporting form (`student/report.html`), client-side validation, photo upload with preview, `POST /api/issues`, `GET /api/issues/mine`, detail view (`student/issue.html`), and timeline stepper.
- [x] **Phase 4 — Admin & Staff Operations:** Operations dashboard (`admin/dashboard.html`) with 5 live metric cards, multi-criteria filtering, search, incident triage (`admin/issue.html`), smart technician dispatch with department recommendations, strict status lifecycle transitions (`Open → Assigned → In Progress → Resolved`), and technician queue (`staff/tasks.html`).
- [x] **Phase 5 & 6 — Smart Suggestions & Duplicate Detection:**
  - `POST /api/ai/suggest`: Rule-based NLP engine analyzing symptoms, safety hazards, and disruptions. Returns category, priority (Low/Med/High/Critical), trimmed summary, confidence score (0.30–0.95), and `source: "rules"`.
  - `POST /api/issues/check-duplicates`: Location + category candidate filtering within the past 30 days. Scores similarity via hybrid Jaccard token overlap + difflib SequenceMatcher string distance with room and category bonuses.
  - `POST /api/issues/{id}/support`: Community upvoting allowing students to support existing open issues rather than creating duplicate tickets.
  - Form prefilling with interactive "✨ Smart suggestion" badge and review-step duplicate detection card with one-click support.
- [x] **Phase 7 — Operations Analytics:**
  - 8 admin-only analytics endpoints: summary, category split, block split, status breakdown, 30-day continuous daily trend, recurring problem hotspots, block × category intensity heatmap matrix, and average resolution turnaround hours.
  - Chart.js powered dark-mode dashboard (`admin/analytics.html`) with doughnut, bar, line, and heatmap table visualizations.
- [x] **Phase 8 — In-App Notifications, Docs & Tests:**
  - `notifications` relational table and endpoints (`GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`).
  - Notification bell with unread count badge in navbar across student, admin, and staff pages with dropdown list and XSS-safe `textContent` rendering.
  - Automated test suite covering auth, issues, duplicate detection, rule-based suggestions, analytics authorization, and notifications.
  - 3-minute pitch demo script in `docs/demo-script.md`.

---

## 1. The Problem

Everyday campus problems — broken projectors, lights, fans, chairs, leaking taps, Wi-Fi failures, damaged doors, cleanliness issues — are reported informally through faculty, WhatsApp groups, or verbally. This causes:

- Delays and lost complaints
- Duplicate complaints for the same issue
- No visibility for management
- No way for students to know whether their issue is being handled

**Core question:** How can a campus make it easy to report a problem and ensure it moves from *report → action → resolution*?

---

## 2. The Solution

FixFlow provides **one centralized workflow**:

- A **student** submits a report with a short description, photo, category, and location.
- **Rule-based AI** suggests category, priority, and a short summary, and detects duplicate reports so students can *support* an existing issue instead of creating a new ticket.
- **Management (admin)** sees it on a live dashboard, prioritizes it, assigns it to the right staff member, and updates its status until resolved.
- **Staff** see issues assigned to them and update progress.
- **In-App Notifications** notify students and technicians at every stage.
- **Analytics** reveal recurring problem areas, category distribution, and average turnaround times.

---

## 3. User Roles

| Role | Permissions & Capabilities |
|------|----------------------------|
| **student** | Register/login, report issues, upload photos, view *My Reports*, track status timeline, support existing duplicate issues, comment on own issues, receive status notifications |
| **admin** | View all issues, filter & search, triage priority/category, assign to staff technicians, change status, comment, view operations analytics dashboard |
| **staff** | Login, view assigned tasks queue (`staff/tasks.html`), update status (In Progress / Resolved), comment on assigned tickets |

---

## 4. Priority & Status Definitions

**Priority levels**
| Priority | Meaning | Detection Keywords |
|----------|---------|-------------------|
| **Critical** | Safety risk / hazard / major structural disruption | `spark`, `shock`, `fire`, `smoke`, `flood`, `gas`, `exposed wire`, `collapse` |
| **High** | Blocks teaching or essential facility service | `not working`, `no water`, `no wifi`, `leak`, `broken`, `damaged`, `dead` |
| **Medium** | Inconvenient but usable (default) | Standard maintenance requests |
| **Low** | Cosmetic / minor aesthetic flaw | `scratch`, `paint`, `dust`, `minor`, `cosmetic`, `faded`, `peel` |

**Status flow (strict lifecycle):** `Open → Assigned → In Progress → Resolved`
- Admin can advance one step or jump directly to `Resolved`.
- Reopening a `Resolved` issue back to `Open` is restricted to administrators only.
- Every status change is immutably recorded in `status_history` with timestamp and actor ID.

---

## 5. Tech Stack

| Layer | Technology | Description |
|-------|------------|-------------|
| **Frontend** | Vanilla HTML5 + CSS3 + ES6 JavaScript | Zero build step, Fetch API client, Chart.js via CDN for analytics, dark theme |
| **Backend** | Python 3.12 + FastAPI | High-performance asynchronous REST API, Pydantic validation, interactive Swagger docs at `/docs` |
| **ORM & DB** | SQLAlchemy 2.x + PyMySQL | Parameterized relational queries, foreign keys, cascade deletes, pooling |
| **Database** | MySQL 8 | Relational database hosting users, issues, assignments, comments, supporters, history, and notifications |
| **Security** | JWT + Passlib (Bcrypt) | Stateless bearer tokens (12h expiry), bcrypt password hashing |
| **Photo Storage** | Local Disk (`backend/uploads/`) | UUID-renamed uploads served directly at `/uploads/` |
| **AI Engine** | Rule-Based Deterministic NLP | Keyword mapping, confidence calculation (0.30–0.95), summary extraction; never blocks or fails |
| **Future Scope** | Cloud Providers (AWS) | Modular interfaces allow future integration of AWS S3, RDS, Bedrock, and SES |

---

## 6. REST API Specification

Base path: `/api`. All protected routes require header `Authorization: Bearer <jwt>`. Interactive documentation auto-generated at `/docs`.

### Authentication
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/auth/register` | Register new student `{name, email, password}` | Public |
| POST | `/api/auth/login` | Authenticate and obtain JWT `{access_token, user}` | Public |
| GET | `/api/auth/me` | Fetch authenticated user profile | Authenticated |

### Meta
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/meta/options` | Categories, blocks, priorities, statuses | Public |
| GET | `/api/meta/staff` | List of technicians with department teams | Admin |

### Issues & Student Workflow
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/issues` | Submit new report (multipart form: title, description, category, block, room, priority, image?) | Student |
| GET | `/api/issues/mine` | Student's own issues (supports `?status=`) | Student |
| GET | `/api/issues/{id}` | Full issue details, timeline stepper, assignment, and comments | Involved / Admin / Staff |
| POST | `/api/issues/check-duplicates` | Scan active issues in same block/room for duplicates | Authenticated |
| POST | `/api/issues/{id}/support` | Upvote/support an existing issue (one vote per user) | Authenticated |
| POST | `/api/issues/{id}/comments` | Post a discussion note or work comment | Involved Users |
| GET | `/api/issues/{id}/comments` | Fetch comments for an issue | Involved Users |
| PATCH | `/api/issues/{id}/status` | Advance lifecycle status (`Open → Assigned → In Progress → Resolved`) | Admin / Assigned Staff |

### Smart Suggestions
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/ai/suggest` | Rule-based inference: `{description, category?, block?, room?}` → `{category, priority, summary, confidence, source: "rules"}` | Public / Authenticated |

### Admin Operations & Staff Tasks
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/admin/issues` | Paginated incident list with filters: `status, category, block, priority, q, sortBy, page, page_size` | Admin |
| PATCH | `/api/admin/issues/{id}` | Triage priority and category | Admin |
| POST | `/api/admin/issues/{id}/assign` | Assign issue to technician `{staff_id}`, sets status to `Assigned` | Admin |
| GET | `/api/staff/tasks` | Task queue of issues assigned to logged-in technician | Staff |

### Analytics
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/analytics/summary` | High-level metrics: `{total, open, assigned, in_progress, resolved, critical}` | Admin |
| GET | `/api/analytics/by-category` | Issue counts grouped by category | Admin |
| GET | `/api/analytics/by-block` | Issue counts grouped by campus block | Admin |
| GET | `/api/analytics/by-status` | Issue counts grouped by status | Admin |
| GET | `/api/analytics/trend?days=30` | Daily issue creation counts for the last N days | Admin |
| GET | `/api/analytics/hotspots` | Top recurrent location hotspots (Block + Room) | Admin |
| GET | `/api/analytics/heatmap` | Block × Category count matrix for density heatmap | Admin |
| GET | `/api/analytics/resolution-time` | Average resolution turnaround in hours for resolved tickets | Admin |

### In-App Notifications
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/notifications` | List user's notifications (newest first) | Authenticated |
| POST | `/api/notifications/{id}/read` | Mark specific notification as read | Authenticated |
| POST | `/api/notifications/read-all` | Mark all user's notifications as read | Authenticated |

### System Health
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/health` | Reports status, database connection, storage backend ("local"), and suggestion mode ("rules") | Public |

---

## 7. Running the Project Locally

### Prerequisites
- Python 3.11 or 3.12
- MySQL Server 8.0 running locally

### Step-by-Step Setup

```bash
# 1. Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (.env)
# Create .env from .env.example if not already created
# Ensure DB_USER and DB_PASSWORD match your local MySQL configuration

# 4. Seed the database (creates schema, demo accounts, and 25 realistic issues)
python backend/seed.py

# 5. Start the FastAPI development server
uvicorn backend.app.main:app --reload --port 8000
```

Open your browser to:
- **Application Frontend:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 8. Seeded Demo Accounts

All demo accounts use password: `Demo@1234`

| Role | Email | Password | What to Test |
|------|-------|----------|--------------|
| **Admin** | `admin@fixflow.demo` | `Demo@1234` | Operations dashboard, triage, assignment, status updates, analytics |
| **Staff (Electrical)** | `electric@fixflow.demo` | `Demo@1234` | Electrical task queue, progress updates |
| **Staff (IT)** | `it@fixflow.demo` | `Demo@1234` | IT task queue, projector/equipment repairs |
| **Staff (Plumbing)** | `plumbing@fixflow.demo` | `Demo@1234` | Plumbing task queue |
| **Student 1** | `student1@fixflow.demo` | `Demo@1234` | Report issues with photos, track status, view notifications |
| **Student 2** | `student2@fixflow.demo` | `Demo@1234` | Duplicate detection demo, support existing tickets |

---

## 9. Running Automated Tests

Run the full pytest suite:

```bash
.\venv\Scripts\pytest
```

All 26 automated unit and integration tests will run and pass:
- `tests/test_phase3.py`: Issue creation, photo upload, student access restrictions (403), comments.
- `tests/test_phase4.py`: Admin dashboard, filtering, triage, assignment, strict forward status lifecycle rules, staff queue.
- `tests/test_step_a.py`: Rule-based AI suggestions engine, `/api/ai/suggest`, duplicate detection scoring on near-duplicate pair, and support rules.
- `tests/test_step_b.py`: All 8 analytics endpoints, data structure validation, role authorization guards (403 for non-admins).
- `tests/test_step_c.py`: System health check endpoint, notification generation on assignment and status change, mark-as-read endpoints.

---

## 10. 3-Minute Demo Flow

See [`docs/demo-script.md`](file:///e:/AXON%20FixFlow/docs/demo-script.md) for the exact 3-minute pitch presentation flow with timed cues, verbatim text inputs, and highlighted system behaviors.

---

## 11. Future Scope (Cloud Extensions)

FixFlow's modular architecture is designed so the following cloud integrations can be plugged in behind the existing services:
- **AWS S3 (`services/storage.py`):** Private bucket storage with pre-signed GET URLs for image attachments.
- **Amazon Bedrock (`services/ai_service.py`):** Converse API integration with foundation models (e.g. Claude 3 Haiku / Titan) for generative reasoning, retaining the rule engine as an instant zero-latency fallback.
- **Amazon RDS for MySQL:** Managed cloud relational database with automated backups and read replicas.
- **Amazon SES / SNS (`services/notifications.py`):** Email and SMS push alerts for urgent critical safety hazards.
- **AWS EC2 / App Runner:** Containerized cloud hosting with autoscaling and HTTPS termination.

---

**FixFlow — Smart campus issue reporting & resolution, from problem to fix in one flow.**
