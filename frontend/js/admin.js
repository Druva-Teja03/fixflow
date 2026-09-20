/**
 * FixFlow Operations Admin JavaScript Helper
 * Powers the Live Incident Management Dashboard and Issue Triage/Assignment.
 */

// Helper to format date strings
function formatDate(dateStr) {
  if (!dateStr) return "N/A";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Helper to create priority badge
function createPriorityBadge(priority) {
  const badge = document.createElement("span");
  badge.className = `badge badge-priority-${priority.toLowerCase()}`;
  badge.textContent = priority;
  return badge;
}

// Helper to create status badge
function createStatusBadge(status) {
  const badge = document.createElement("span");
  const key = status.toLowerCase().replace(" ", "-");
  badge.className = `badge badge-status-${key}`;
  badge.textContent = status;
  return badge;
}

// Team to Category matching heuristic for smart assignment recommendations
function isTeamRecommended(team, category) {
  if (!team || !category) return false;
  const t = team.toLowerCase();
  const c = category.toLowerCase();
  if (t === c) return true;
  if (t === "it" && (c === "internet" || c === "equipment")) return true;
  if (t === "housekeeping" && c === "cleaning") return true;
  if (t === "carpentry" && (c === "furniture" || c === "doors/windows")) return true;
  return false;
}

// ==========================================
// 1. ADMIN DASHBOARD LOGIC
// ==========================================

const adminDashboardState = {
  page: 1,
  pageSize: 10,
  status: "",
  category: "",
  block: "",
  priority: "",
  q: "",
  sortBy: "newest",
};

async function initAdminDashboard() {
  if (!auth.requireAuth(["admin"])) return;

  const user = api.getUser();
  if (user) {
    const greetingEl = document.getElementById("user-greeting");
    if (greetingEl) greetingEl.textContent = `Admin: ${user.name}`;
  }

  // Bind filter events
  setupDashboardFilters();

  // Load summary stats and issues list
  await loadSummaryStats();
  await loadAdminIssues();
}

async function loadSummaryStats() {
  try {
    const summary = await api.get("/analytics/summary");
    const elTotal = document.getElementById("card-total");
    const elOpen = document.getElementById("card-open");
    const elInProg = document.getElementById("card-in-progress");
    const elCritical = document.getElementById("card-critical");
    const elResolved = document.getElementById("card-resolved");

    if (elTotal) elTotal.textContent = summary.total;
    if (elOpen) elOpen.textContent = summary.open;
    if (elInProg) elInProg.textContent = summary.in_progress;
    if (elCritical) elCritical.textContent = summary.critical;
    if (elResolved) elResolved.textContent = summary.resolved;
  } catch (err) {
    console.error("Failed to load analytics summary:", err);
    showToast("Failed to load dashboard metrics.", "error");
  }
}

function setupDashboardFilters() {
  const statusFilter = document.getElementById("filter-status");
  const catFilter = document.getElementById("filter-category");
  const blockFilter = document.getElementById("filter-block");
  const prioFilter = document.getElementById("filter-priority");
  const searchInput = document.getElementById("filter-search");
  const sortSelect = document.getElementById("filter-sort");
  const btnReset = document.getElementById("btn-reset-filters");

  if (statusFilter) {
    statusFilter.addEventListener("change", () => {
      adminDashboardState.status = statusFilter.value;
      adminDashboardState.page = 1;
      loadAdminIssues();
    });
  }

  if (catFilter) {
    catFilter.addEventListener("change", () => {
      adminDashboardState.category = catFilter.value;
      adminDashboardState.page = 1;
      loadAdminIssues();
    });
  }

  if (blockFilter) {
    blockFilter.addEventListener("change", () => {
      adminDashboardState.block = blockFilter.value;
      adminDashboardState.page = 1;
      loadAdminIssues();
    });
  }

  if (prioFilter) {
    prioFilter.addEventListener("change", () => {
      adminDashboardState.priority = prioFilter.value;
      adminDashboardState.page = 1;
      loadAdminIssues();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      adminDashboardState.sortBy = sortSelect.value;
      adminDashboardState.page = 1;
      loadAdminIssues();
    });
  }

  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        adminDashboardState.q = searchInput.value.trim();
        adminDashboardState.page = 1;
        loadAdminIssues();
      }, 350);
    });
  }

  if (btnReset) {
    btnReset.addEventListener("click", () => {
      adminDashboardState.page = 1;
      adminDashboardState.status = "";
      adminDashboardState.category = "";
      adminDashboardState.block = "";
      adminDashboardState.priority = "";
      adminDashboardState.q = "";
      adminDashboardState.sortBy = "newest";

      if (statusFilter) statusFilter.value = "";
      if (catFilter) catFilter.value = "";
      if (blockFilter) blockFilter.value = "";
      if (prioFilter) prioFilter.value = "";
      if (searchInput) searchInput.value = "";
      if (sortSelect) sortSelect.value = "newest";

      loadAdminIssues();
    });
  }
}

async function loadAdminIssues() {
  const container = document.getElementById("issues-table-container");
  if (!container) return;

  // Render spinner
  container.innerHTML = `
    <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
      <div class="spinner"></div>
      <p style="margin-top: 0.75rem; font-size: 0.9rem;">Loading campus incident records...</p>
    </div>
  `;

  try {
    const params = new URLSearchParams({
      page: adminDashboardState.page,
      page_size: adminDashboardState.pageSize,
      sort_by: adminDashboardState.sortBy,
    });

    if (adminDashboardState.status) params.append("status", adminDashboardState.status);
    if (adminDashboardState.category) params.append("category", adminDashboardState.category);
    if (adminDashboardState.block) params.append("block", adminDashboardState.block);
    if (adminDashboardState.priority) params.append("priority", adminDashboardState.priority);
    if (adminDashboardState.q) params.append("q", adminDashboardState.q);

    const data = await api.get(`/admin/issues?${params.toString()}`);
    renderAdminIssuesTable(data);
  } catch (err) {
    console.error("Failed to load admin issues:", err);
    container.innerHTML = `
      <div style="text-align: center; padding: 2.5rem; color: #ef4444;">
        <p style="font-weight: 600; margin-bottom: 0.5rem;">Failed to load issues</p>
        <p style="font-size: 0.85rem; color: var(--text-muted);">${err.message || "An unexpected error occurred."}</p>
        <button onclick="loadAdminIssues()" class="btn btn-outline btn-sm" style="margin-top: 1rem;">Retry</button>
      </div>
    `;
  }
}

function renderAdminIssuesTable(data) {
  const container = document.getElementById("issues-table-container");
  if (!container) return;
  container.innerHTML = "";

  const issues = data.items || [];

  if (issues.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 3.5rem 1rem; color: var(--text-muted);">
        <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem; color: #fff;">No matching issues found</p>
        <p style="font-size: 0.875rem;">Try clearing filters or adjusting your search keyword.</p>
      </div>
    `;
    return;
  }

  const tableWrapper = document.createElement("div");
  tableWrapper.className = "table-responsive";

  const table = document.createElement("table");
  table.className = "table";

  table.innerHTML = `
    <thead>
      <tr>
        <th style="width: 70px;">ID</th>
        <th>Issue Title</th>
        <th>Category</th>
        <th>Location</th>
        <th>Priority</th>
        <th>Status</th>
        <th>Support</th>
        <th>Reporter</th>
        <th>Assigned Technician</th>
        <th>Reported On</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;

  const tbody = table.querySelector("tbody");

  issues.forEach((iss) => {
    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    tr.addEventListener("click", () => {
      window.location.href = `/admin/issue.html?id=${iss.issue_id}`;
    });

    // ID
    const tdId = document.createElement("td");
    tdId.style.fontWeight = "700";
    tdId.style.color = "var(--primary)";
    tdId.textContent = `#${iss.issue_id}`;
    tr.appendChild(tdId);

    // Title
    const tdTitle = document.createElement("td");
    const link = document.createElement("a");
    link.href = `/admin/issue.html?id=${iss.issue_id}`;
    link.style.fontWeight = "600";
    link.textContent = iss.title;
    tdTitle.appendChild(link);
    tr.appendChild(tdTitle);

    // Category
    const tdCat = document.createElement("td");
    const catBadge = document.createElement("span");
    catBadge.className = "badge";
    catBadge.style.background = "#334155";
    catBadge.textContent = iss.category;
    tdCat.appendChild(catBadge);
    tr.appendChild(tdCat);

    // Location
    const tdLoc = document.createElement("td");
    tdLoc.textContent = iss.room ? `${iss.block} - ${iss.room}` : iss.block;
    tr.appendChild(tdLoc);

    // Priority
    const tdPrio = document.createElement("td");
    tdPrio.appendChild(createPriorityBadge(iss.priority));
    tr.appendChild(tdPrio);

    // Status
    const tdStat = document.createElement("td");
    tdStat.appendChild(createStatusBadge(iss.status));
    tr.appendChild(tdStat);

    // Support
    const tdSupp = document.createElement("td");
    tdSupp.style.fontWeight = "600";
    tdSupp.textContent = `👍 ${iss.support_count}`;
    tr.appendChild(tdSupp);

    // Reporter
    const tdRep = document.createElement("td");
    tdRep.textContent = iss.reporter_name;
    tr.appendChild(tdRep);

    // Assigned Technician
    const tdStaff = document.createElement("td");
    if (iss.assigned_staff_name) {
      const staffBadge = document.createElement("span");
      staffBadge.className = "badge";
      staffBadge.style.background = "rgba(139, 92, 246, 0.2)";
      staffBadge.style.color = "#c084fc";
      staffBadge.style.border = "1px solid rgba(139, 92, 246, 0.4)";
      staffBadge.textContent = `${iss.assigned_staff_name} (${iss.assigned_staff_team || "General"})`;
      tdStaff.appendChild(staffBadge);
    } else {
      const unassigned = document.createElement("span");
      unassigned.className = "badge";
      unassigned.style.background = "rgba(255, 255, 255, 0.06)";
      unassigned.style.color = "var(--text-muted)";
      unassigned.textContent = "Unassigned";
      tdStaff.appendChild(unassigned);
    }
    tr.appendChild(tdStaff);

    // Created At
    const tdDate = document.createElement("td");
    tdDate.style.fontSize = "0.8rem";
    tdDate.style.color = "var(--text-muted)";
    tdDate.textContent = formatDate(iss.created_at);
    tr.appendChild(tdDate);

    tbody.appendChild(tr);
  });

  tableWrapper.appendChild(table);
  container.appendChild(tableWrapper);

  // Render pagination bar
  renderPagination(data, container);
}

function renderPagination(data, parentContainer) {
  const bar = document.createElement("div");
  bar.style.display = "flex";
  bar.style.justifyContent = "space-between";
  bar.style.alignItems = "center";
  bar.style.flexWrap = "wrap";
  bar.style.gap = "1rem";
  bar.style.marginTop = "1.25rem";
  bar.style.paddingTop = "1rem";
  bar.style.borderTop = "1px solid var(--border-color)";

  // Info
  const info = document.createElement("div");
  info.style.fontSize = "0.875rem";
  info.style.color = "var(--text-muted)";
  const start = (data.page - 1) * data.page_size + (data.total > 0 ? 1 : 0);
  const end = Math.min(data.page * data.page_size, data.total);
  info.textContent = `Showing ${start} to ${end} of ${data.total} incidents (Page ${data.page} of ${data.total_pages})`;
  bar.appendChild(info);

  // Controls
  const controls = document.createElement("div");
  controls.style.display = "flex";
  controls.style.gap = "0.5rem";

  const btnPrev = document.createElement("button");
  btnPrev.className = "btn btn-outline btn-sm";
  btnPrev.textContent = "← Previous";
  btnPrev.disabled = data.page <= 1;
  btnPrev.addEventListener("click", () => {
    if (adminDashboardState.page > 1) {
      adminDashboardState.page--;
      loadAdminIssues();
    }
  });
  controls.appendChild(btnPrev);

  const btnNext = document.createElement("button");
  btnNext.className = "btn btn-outline btn-sm";
  btnNext.textContent = "Next →";
  btnNext.disabled = data.page >= data.total_pages;
  btnNext.addEventListener("click", () => {
    if (adminDashboardState.page < data.total_pages) {
      adminDashboardState.page++;
      loadAdminIssues();
    }
  });
  controls.appendChild(btnNext);

  bar.appendChild(controls);
  parentContainer.appendChild(bar);
}

// ==========================================
// 2. ADMIN ISSUE DETAIL & TRIAGE LOGIC
// ==========================================

let currentAdminIssue = null;
let allStaffMembers = [];

async function initAdminIssue() {
  if (!auth.requireAuth(["admin"])) return;

  const urlParams = new URLSearchParams(window.location.search);
  const issueId = urlParams.get("id");

  if (!issueId) {
    window.location.href = "/admin/dashboard.html";
    return;
  }

  const user = api.getUser();
  if (user) {
    const greetingEl = document.getElementById("user-greeting");
    if (greetingEl) greetingEl.textContent = `Admin: ${user.name}`;
  }

  // 1. Fetch Staff list for dropdown
  try {
    allStaffMembers = await api.get("/meta/staff");
  } catch (err) {
    console.error("Failed to load staff list:", err);
  }

  // 2. Fetch issue details
  await loadAdminIssueDetails(issueId);

  // 3. Setup comment submission
  setupAdminCommentSubmission(issueId);
}

async function loadAdminIssueDetails(issueId) {
  try {
    const issue = await api.get(`/issues/${issueId}`);
    currentAdminIssue = issue;
    renderAdminIssueDetails(issue);
  } catch (err) {
    console.error("Failed to load issue details:", err);
    const mainEl = document.getElementById("issue-detail-main");
    if (mainEl) {
      mainEl.innerHTML = `
        <div class="card" style="text-align: center; padding: 3rem; color: #ef4444;">
          <h2>Issue Not Found</h2>
          <p style="color: var(--text-muted); margin: 1rem 0;">${err.message || "Failed to load incident details."}</p>
          <a href="/admin/dashboard.html" class="btn btn-primary">← Return to Dashboard</a>
        </div>
      `;
    }
  }
}

function renderAdminIssueDetails(issue) {
  // Title & ID
  document.getElementById("detail-id").textContent = `#${issue.issue_id}`;
  document.getElementById("detail-title").textContent = issue.title;

  // Header Badges
  const badgeContainer = document.getElementById("detail-badges");
  badgeContainer.innerHTML = "";
  badgeContainer.appendChild(createStatusBadge(issue.status));
  badgeContainer.appendChild(createPriorityBadge(issue.priority));

  const catBadge = document.createElement("span");
  catBadge.className = "badge";
  catBadge.style.background = "#334155";
  catBadge.textContent = issue.category;
  badgeContainer.appendChild(catBadge);

  // Description
  document.getElementById("detail-desc").textContent = issue.description;

  // AI Smart Summary
  const aiBox = document.getElementById("detail-ai-summary-container");
  const aiText = document.getElementById("detail-ai-summary");
  if (aiBox && aiText) {
    if (issue.ai_summary) {
      aiText.textContent = issue.ai_summary;
      aiBox.style.display = "block";
    } else {
      aiBox.style.display = "none";
    }
  }

  // Location
  const locParts = [issue.block];
  if (issue.building) locParts.push(issue.building);
  if (issue.room) locParts.push(issue.room);
  document.getElementById("detail-location").textContent = locParts.join(" / ");

  // Metadata
  document.getElementById("detail-reporter").textContent = `${issue.reporter_name} (${issue.reporter_email || "Student"})`;
  document.getElementById("detail-created").textContent = formatDate(issue.created_at);
  document.getElementById("detail-support-count").textContent = issue.support_count;

  // Photo
  const photoContainer = document.getElementById("detail-photo-container");
  if (issue.image_url) {
    photoContainer.style.display = "block";
    const imgEl = document.getElementById("detail-photo");
    imgEl.src = issue.image_url;
    const linkEl = document.getElementById("detail-photo-link");
    if (linkEl) linkEl.href = issue.image_url;
  } else {
    photoContainer.style.display = "none";
  }

  // --- Render Control Panels ---
  renderTriageControls(issue);
  renderAssignmentControls(issue);
  renderStatusWorkflowButtons(issue);

  // --- Render Stepper Timeline ---
  renderAdminStatusStepper(issue.status, issue.status_history);

  // --- Render Comments ---
  renderAdminComments(issue.comments);
}

function renderTriageControls(issue) {
  const prioritySelect = document.getElementById("triage-priority");
  const categorySelect = document.getElementById("triage-category");
  const btnSave = document.getElementById("btn-save-triage");

  if (prioritySelect) prioritySelect.value = issue.priority;
  if (categorySelect) categorySelect.value = issue.category;

  if (btnSave) {
    // Clone node to strip old listeners
    const newBtn = btnSave.cloneNode(true);
    btnSave.parentNode.replaceChild(newBtn, btnSave);

    newBtn.addEventListener("click", async () => {
      newBtn.disabled = true;
      try {
        await api.patch(`/admin/issues/${issue.issue_id}`, {
          priority: prioritySelect.value,
          category: categorySelect.value,
        });
        showToast("Issue priority & category updated successfully!", "success");
        await loadAdminIssueDetails(issue.issue_id);
      } catch (err) {
        showToast(err.message || "Failed to update triage.", "error");
      } finally {
        newBtn.disabled = false;
      }
    });
  }
}

function renderAssignmentControls(issue) {
  const staffSelect = document.getElementById("assign-staff-select");
  const btnAssign = document.getElementById("btn-assign-staff");
  const assignmentInfoEl = document.getElementById("current-assignment-info");

  if (!staffSelect || !btnAssign) return;

  staffSelect.innerHTML = '<option value="">-- Select Technician / Staff Member --</option>';

  const assignedStaffId = issue.assignment ? issue.assignment.staff_id : null;

  if (issue.assignment && assignmentInfoEl) {
    assignmentInfoEl.textContent = `Currently assigned to: ${issue.assignment.staff_name} (${issue.assignment.staff_team || "Maintenance"}) by ${issue.assignment.assigned_by_name} on ${formatDate(issue.assignment.assigned_at)}`;
    assignmentInfoEl.style.display = "block";
  } else if (assignmentInfoEl) {
    assignmentInfoEl.textContent = "Status: Unassigned. Select a staff technician below.";
    assignmentInfoEl.style.display = "block";
  }

  // Populate staff dropdown with smart team matching
  allStaffMembers.forEach((staff) => {
    const opt = document.createElement("option");
    opt.value = staff.user_id;

    const isRecommended = isTeamRecommended(staff.team, issue.category);
    const star = isRecommended ? "⭐ " : "";
    const recTag = isRecommended ? ` — Recommended for ${issue.category}` : "";
    opt.textContent = `${star}${staff.name} [${staff.team || "General"}]${recTag}`;

    if (staff.user_id === assignedStaffId) {
      opt.selected = true;
    }

    staffSelect.appendChild(opt);
  });

  // Rebind assign button
  const newBtn = btnAssign.cloneNode(true);
  btnAssign.parentNode.replaceChild(newBtn, btnAssign);

  newBtn.addEventListener("click", async () => {
    const selectedStaffId = staffSelect.value;
    if (!selectedStaffId) {
      showToast("Please choose a staff technician to assign.", "error");
      return;
    }

    newBtn.disabled = true;
    try {
      await api.post(`/admin/issues/${issue.issue_id}/assign`, {
        staff_id: parseInt(selectedStaffId, 10),
      });
      showToast("Technician assigned successfully!", "success");
      await loadAdminIssueDetails(issue.issue_id);
    } catch (err) {
      showToast(err.message || "Failed to assign technician.", "error");
    } finally {
      newBtn.disabled = false;
    }
  });
}

function renderStatusWorkflowButtons(issue) {
  const container = document.getElementById("status-action-buttons");
  if (!container) return;
  container.innerHTML = "";

  const curr = issue.status;

  // Admin status transition options:
  // Open -> Assigned (usually via Assign Staff, but can mark resolved directly)
  // Assigned -> In Progress or Resolved
  // In Progress -> Resolved
  // Resolved -> Open (reopen)

  if (curr === "Open") {
    const btnResolve = document.createElement("button");
    btnResolve.className = "btn btn-primary btn-sm";
    btnResolve.textContent = "✓ Fast Resolve Ticket";
    btnResolve.title = "Directly mark this issue as Resolved without technician dispatch.";
    btnResolve.addEventListener("click", () => handleAdminStatusUpdate(issue.issue_id, "Resolved"));
    container.appendChild(btnResolve);
  } else if (curr === "Assigned") {
    const btnInProg = document.createElement("button");
    btnInProg.className = "btn btn-secondary btn-sm";
    btnInProg.style.color = "var(--status-in-progress)";
    btnInProg.textContent = "▶ Advance to In Progress";
    btnInProg.addEventListener("click", () => handleAdminStatusUpdate(issue.issue_id, "In Progress"));
    container.appendChild(btnInProg);

    const btnResolve = document.createElement("button");
    btnResolve.className = "btn btn-primary btn-sm";
    btnResolve.textContent = "✓ Mark Resolved";
    btnResolve.addEventListener("click", () => handleAdminStatusUpdate(issue.issue_id, "Resolved"));
    container.appendChild(btnResolve);
  } else if (curr === "In Progress") {
    const btnResolve = document.createElement("button");
    btnResolve.className = "btn btn-primary btn-sm";
    btnResolve.textContent = "✓ Mark Issue Resolved";
    btnResolve.addEventListener("click", () => handleAdminStatusUpdate(issue.issue_id, "Resolved"));
    container.appendChild(btnResolve);
  } else if (curr === "Resolved") {
    const btnReopen = document.createElement("button");
    btnReopen.className = "btn btn-danger btn-sm";
    btnReopen.textContent = "↺ Reopen Issue (Set to Open)";
    btnReopen.title = "Reopen this ticket if issue re-occurs or was not fully resolved.";
    btnReopen.addEventListener("click", () => {
      if (confirm("Are you sure you want to reopen this resolved ticket?")) {
        handleAdminStatusUpdate(issue.issue_id, "Open");
      }
    });
    container.appendChild(btnReopen);
  }
}

async function handleAdminStatusUpdate(issueId, targetStatus) {
  try {
    await api.patch(`/issues/${issueId}/status`, { status: targetStatus });
    showToast(`Status successfully updated to '${targetStatus}'.`, "success");
    await loadAdminIssueDetails(issueId);
  } catch (err) {
    showToast(err.message || "Failed to update status.", "error");
  }
}

function renderAdminStatusStepper(currentStatus, history) {
  const steps = ["Open", "Assigned", "In Progress", "Resolved"];
  const currentIdx = steps.indexOf(currentStatus);

  const container = document.getElementById("admin-stepper-container");
  if (!container) return;
  container.innerHTML = "";

  const stepper = document.createElement("div");
  stepper.style.display = "flex";
  stepper.style.justifyContent = "space-between";
  stepper.style.position = "relative";
  stepper.style.margin = "1.5rem 0";

  steps.forEach((stepName, idx) => {
    const isCompleted = idx <= currentIdx;
    const isCurrent = idx === currentIdx;

    const stepItem = document.createElement("div");
    stepItem.style.display = "flex";
    stepItem.style.flexDirection = "column";
    stepItem.style.alignItems = "center";
    stepItem.style.position = "relative";
    stepItem.style.zIndex = "2";
    stepItem.style.flex = "1";

    const circle = document.createElement("div");
    circle.style.width = "34px";
    circle.style.height = "34px";
    circle.style.borderRadius = "50%";
    circle.style.display = "flex";
    circle.style.alignItems = "center";
    circle.style.justifyContent = "center";
    circle.style.fontSize = "0.85rem";
    circle.style.fontWeight = "700";
    circle.style.marginBottom = "0.4rem";

    if (isCurrent) {
      circle.style.background = "var(--primary)";
      circle.style.color = "#fff";
      circle.style.boxShadow = "0 0 14px var(--primary-glow)";
      circle.textContent = idx + 1;
    } else if (isCompleted) {
      circle.style.background = "var(--status-resolved)";
      circle.style.color = "#fff";
      circle.textContent = "✓";
    } else {
      circle.style.background = "#334155";
      circle.style.color = "var(--text-muted)";
      circle.textContent = idx + 1;
    }

    const label = document.createElement("span");
    label.style.fontSize = "0.8rem";
    label.style.fontWeight = isCurrent ? "700" : "500";
    label.style.color = isCompleted ? "#fff" : "var(--text-muted)";
    label.textContent = stepName;

    stepItem.appendChild(circle);
    stepItem.appendChild(label);
    stepper.appendChild(stepItem);
  });

  container.appendChild(stepper);

  // History timeline audit table
  const historyList = document.getElementById("admin-history-list");
  if (!historyList) return;
  historyList.innerHTML = "";

  if (history && history.length > 0) {
    const hTitle = document.createElement("h4");
    hTitle.style.fontSize = "0.85rem";
    hTitle.style.color = "var(--text-muted)";
    hTitle.style.textTransform = "uppercase";
    hTitle.style.marginTop = "1rem";
    hTitle.style.marginBottom = "0.5rem";
    hTitle.textContent = "Audit Trail & Historical Changes";
    historyList.appendChild(hTitle);

    history.forEach((h) => {
      const row = document.createElement("div");
      row.style.fontSize = "0.85rem";
      row.style.padding = "0.5rem 0";
      row.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
      row.style.display = "flex";
      row.style.justifyContent = "space-between";
      row.style.flexWrap = "wrap";
      row.style.gap = "0.5rem";

      const left = document.createElement("span");
      const transText = h.old_status ? `${h.old_status} → ${h.new_status}` : h.new_status;
      left.textContent = `Status changed to ${transText} by ${h.changed_by_name || "System"}`;
      row.appendChild(left);

      const right = document.createElement("span");
      right.style.color = "var(--text-muted)";
      right.textContent = formatDate(h.changed_at);
      row.appendChild(right);

      historyList.appendChild(row);
    });
  }
}

function renderAdminComments(comments) {
  const container = document.getElementById("admin-comments-list");
  if (!container) return;
  container.innerHTML = "";

  if (!comments || comments.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No comments recorded for this ticket yet.</p>';
    return;
  }

  comments.forEach((c) => {
    const box = document.createElement("div");
    box.style.background = "rgba(15, 23, 42, 0.4)";
    box.style.border = "1px solid var(--border-color)";
    box.style.borderRadius = "var(--radius-md)";
    box.style.padding = "0.85rem 1rem";
    box.style.marginBottom = "0.75rem";

    const header = document.createElement("div");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.marginBottom = "0.35rem";
    header.style.fontSize = "0.8rem";

    const authorSpan = document.createElement("span");
    authorSpan.style.fontWeight = "700";
    authorSpan.style.color = "#fff";
    authorSpan.textContent = `${c.user_name} (${c.user_role.toUpperCase()})`;
    header.appendChild(authorSpan);

    const timeSpan = document.createElement("span");
    timeSpan.style.color = "var(--text-muted)";
    timeSpan.textContent = formatDate(c.created_at);
    header.appendChild(timeSpan);

    const body = document.createElement("div");
    body.style.fontSize = "0.9rem";
    body.style.color = "var(--text-sub)";
    body.style.whiteSpace = "pre-wrap";
    body.textContent = c.comment;

    box.appendChild(header);
    box.appendChild(body);
    container.appendChild(box);
  });
}

function setupAdminCommentSubmission(issueId) {
  const form = document.getElementById("admin-comment-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("admin-comment-input");
    const text = input.value.trim();
    if (!text) return;

    const btn = document.getElementById("btn-post-comment");
    btn.disabled = true;

    try {
      await api.post(`/issues/${issueId}/comments`, { comment: text });
      input.value = "";
      showToast("Comment posted successfully.", "success");
      await loadAdminIssueDetails(issueId);
    } catch (err) {
      showToast(err.message || "Failed to post comment.", "error");
    } finally {
      btn.disabled = false;
    }
  });
}
