# FixFlow — 3-Minute Demo Script

> **Elevator Pitch:** *"FixFlow is a smart campus operations and issue resolution platform that turns unstructured campus complaints into trackable, prioritized, and measurable workflows — powered by rule-based classification, duplicate detection, and real-time operations analytics."*

---

## Demo Summary & Timetable

| Time | Segment | What to Show |
|---|---|---|
| **0:00 – 0:30** | **Problem & Context** | Explain why WhatsApp/informal campus reporting fails: lost issues, duplicate reports, no visibility, and slow turnaround. |
| **0:30 – 1:15** | **Student Reporting & Smart Suggestions** | Log in as Student → Report "Projector not working" in Block A, Room 204 → AI suggests *Equipment / High* → Attach photo → Submit. |
| **1:15 – 2:00** | **Admin Incident Triage & Technician Dispatch** | Log in as Admin → View live metrics → Open ticket → See AI Summary → Assign IT technician → Walk through status progression → In-app notification bell. |
| **2:00 – 2:30** | **Standout Innovation: Duplicate Detection** | Second student reports the same issue in Room 204 → Duplicate card detected → Student clicks **[Support this issue]** → `support_count` increments without ticket clutter. |
| **2:30 – 3:00** | **Campus Operations Analytics** | Open `/admin/analytics.html` → Show Category doughnut, Block bar chart, 30-day trend, problem hotspots ranking, and Block × Category intensity heatmap. |

---

## Demo Accounts (Pre-Seeded)

All demo accounts share the password: `Demo@1234`

| Role | Email | Password | Purpose in Demo |
|---|---|---|---|
| **Campus Admin** | `admin@fixflow.demo` | `Demo@1234` | Triage, technician dispatch, status progression, and analytics |
| **Student 1** | `student1@fixflow.demo` | `Demo@1234` | Original issue reporting & photo upload |
| **Student 2** | `student2@fixflow.demo` | `Demo@1234` | Duplicate detection & community upvoting ("Support") |
| **IT Staff** | `it@fixflow.demo` | `Demo@1234` | Technician task queue and repair status updates |

---

## Step-by-Step Walkthrough

### 1. Problem Setup (0:00 – 0:30)
*Speak to the judges/evaluators:*
> *"In colleges and universities, when a classroom projector stops working, a water pipe leaks, or a switchboard sparks, students complain on WhatsApp groups or tell someone verbally. The result? Complaints are forgotten, duplicate tickets flood maintenance, and students never know if someone is fixing it. FixFlow solves this in one unified flow."*

---

### 2. Student Demo — Smart Suggestion & Ticket Filing (0:30 – 1:15)
1. Navigate to: `http://localhost:8000/`
2. Click **Demo: Student 1** (or enter `student1@fixflow.demo` / `Demo@1234`).
3. Click **Report an Issue** (or **+ Report New Problem** button).
4. **Step 1: Describe the Problem**
   - **Issue Title:** `Projector not working in Room 204`
   - **Detailed Description:** `The overhead projector power switch light is blinking red, and the display lamp does not strike when turned on.`
   - Click **Next →**
5. **Step 2: Smart Classification**
   - **Highlight to judges:** Notice the purple badge: **✨ Smart suggestion (75% match)**.
   - Category was automatically selected as **Equipment**.
   - Priority was automatically escalated to **High** (teaching disruption).
   - Point out: *"The student can freely edit or override these suggestions if needed."*
   - Click **Next →**
6. **Step 3: Location**
   - Campus Block: `Block A`
   - Building / Floor: `Engineering Block / 2nd Floor`
   - Room: `Room 204`
   - Click **Next →**
7. **Step 4: Attach Photo (Optional)**
   - Upload any sample picture or skip.
   - Click **Next →**
8. **Step 5: Review & Submit**
   - Review details and click **✓ Submit Issue Report**.
   - Issue is created with status **Open** in *My Reports*.

---

### 3. Admin Operations & Smart Dispatch (1:15 – 2:00)
1. Click **Logout** at top right.
2. Click **Demo: Admin** (or enter `admin@fixflow.demo` / `Demo@1234`).
3. On the **Operations Admin Dashboard**:
   - Point out the 5 live metric cards: Total, Active (Open), In Progress, Critical, and Resolved.
4. Click on the newly reported issue (or Issue `#1`).
5. In the **Incident Triage & Assignment** view:
   - **Highlight:** The **✨ Smart Summary** card: *"Overhead projector power failure with red indicator light blinking."*
   - In **Assign Technician**, open the dropdown.
   - **Highlight:** `⭐ Suresh Kumar [IT] — Recommended for Equipment` is highlighted at the top because FixFlow intelligently matches technician teams with issue categories.
   - Select `Suresh Kumar` and click **Assign Technician**.
   - Status transitions to **Assigned**.
6. Use **Quick Status Progression**:
   - Click **Mark In Progress** → Stepper and audit log advance in real time.
   - Point out the notification bell: both the technician and the student received in-app notifications instantly.

---

### 4. Standout Innovation — Duplicate Detection & Community Support (2:00 – 2:30)
1. Open a new Incognito window (or logout and log in as **Student 2**):
   - Email: `student2@fixflow.demo` | Password: `Demo@1234`
2. Click **Report Issue**.
3. **Step 1:** Enter:
   - **Title:** `Broken projector in lecture room`
   - **Description:** `Projector in Room 204 is completely dead and cannot display lecture presentation slides.`
4. Step 2 & 3:
   - Category: `Equipment`
   - Block: `Block A`
   - Room: `Room 204`
5. Step 4: Skip photo → Click **Next →** to reach **Step 5: Review**.
6. **The Wow Factor:**
   - FixFlow scans active open issues in the same block/room using hybrid token overlap and string distance.
   - An alert card appears:
     > **⚠️ Similar Issue Already Reported**
     > *"Similar issue already reported in Room 204: Projector not working in Room 204, 3 supporters, status Assigned"*
     > `[👍 Support this issue]` `[This is different, submit anyway]`
7. Click **👍 Support this issue**:
   - The student is redirected to their dashboard with a success toast.
   - The existing issue's `support_count` increments to **4**, prioritizing the repair without creating duplicate database records!

---

### 5. Campus Operations Analytics (2:30 – 3:00)
1. Switch back to the **Admin** tab.
2. Click **Analytics** in the top navigation bar (or navigate to `/admin/analytics.html`).
3. Tour the live operational insights:
   - **Avg. Resolution Time:** Displays average turnaround in hours (e.g., ~33.8 hrs) computed from resolved issues.
   - **Issues by Category:** Doughnut chart showing category distribution (Equipment, Electrical, Plumbing, Cleaning...).
   - **Issues by Campus Block:** Bar chart comparing report volume across Block A, B, C, and D.
   - **30-Day Trend Line:** Continuous line chart showing day-by-day issue filing volume.
   - **Campus Problem Hotspots:** Ranks recurring problem locations (Room 204 is flagged at the top).
   - **Block × Category Heatmap:** Intensity matrix revealing where specific categories concentrate across campus.

---

## Key Talking Points for Q&A

1. **Why zero-AWS / local execution?**
   - FixFlow is architected with clear service boundaries (`services/storage.py`, `services/ai_service.py`, `services/notifications.py`).
   - For local development, testing, and offline evaluation, it operates with **local disk storage**, **rule-based NLP inference**, and a **local MySQL database**.
   - Cloud adapters (AWS S3, Amazon Bedrock, RDS) can be plugged behind these service contracts in the future without rewriting core application code.

2. **How does duplicate detection work without machine learning models?**
   - Deterministic candidate filtering: queries open issues in the same block and room from the last 30 days.
   - Scoring algorithm: `0.6 × Jaccard token overlap + 0.4 × difflib SequenceMatcher ratio + 0.2 same room bonus + 0.1 same category bonus` (capped at 1.0).
   - Candidates with score $\ge 0.55$ are presented to the student to prevent duplicate ticket clutter.

3. **How is security handled?**
   - Passwords hashed with bcrypt.
   - Stateless JWT tokens with role-based endpoint guards (`student`, `admin`, `staff`).
   - Students can only access their own issues; unauthorized attempts return `403 Forbidden`.
   - All user-supplied text in the frontend is rendered safely using `textContent` to prevent XSS.
