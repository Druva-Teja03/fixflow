/**
 * FixFlow Student Portal JavaScript Helper
 * Handles Dashboard metrics, My Reports listing with filters,
 * and Issue Detail with status timeline and comments.
 */

// Helper to safely format date
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

// --- STUDENT DASHBOARD ---
async function initDashboard() {
  if (!auth.requireAuth(["student"])) return;

  const user = api.getUser();
  if (user) {
    const greetingEl = document.getElementById("user-greeting");
    if (greetingEl) greetingEl.textContent = `${user.name} (${user.email})`;
    const titleEl = document.getElementById("welcome-title");
    if (titleEl) titleEl.textContent = `Welcome back, ${user.name.split(" ")[0]}!`;
  }

  try {
    const issues = await api.get("/issues/mine");

    let openCount = 0;
    let inProgressCount = 0;
    let resolvedCount = 0;

    issues.forEach((i) => {
      if (i.status === "Open" || i.status === "Assigned") openCount++;
      else if (i.status === "In Progress") inProgressCount++;
      else if (i.status === "Resolved") resolvedCount++;
    });

    const elActive = document.getElementById("stat-active");
    if (elActive) elActive.textContent = openCount;
    const elInProg = document.getElementById("stat-in-progress");
    if (elInProg) elInProg.textContent = inProgressCount;
    const elResolved = document.getElementById("stat-resolved");
    if (elResolved) elResolved.textContent = resolvedCount;
    const elTotal = document.getElementById("stat-total");
    if (elTotal) elTotal.textContent = issues.length;

    renderRecentIssues(issues.slice(0, 5));
  } catch (err) {
    console.error("Failed to load student dashboard:", err);
    showToast("Failed to load your issue stats.", "error");
  }
}

function renderRecentIssues(issues) {
  const container = document.getElementById("recent-issues-container");
  if (!container) return;
  container.innerHTML = "";

  if (issues.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
        <p style="margin-bottom: 1rem;">You have not reported any issues yet.</p>
        <a href="/student/report.html" class="btn btn-primary btn-sm">Report Your First Issue</a>
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
        <th>Issue</th>
        <th>Category</th>
        <th>Location</th>
        <th>Priority</th>
        <th>Status</th>
        <th>Reported On</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;

  const tbody = table.querySelector("tbody");

  issues.forEach((item) => {
    const tr = document.createElement("tr");
    tr.addEventListener("click", () => {
      window.location.href = `/student/issue.html?id=${item.issue_id}`;
    });

    // Title
    const tdTitle = document.createElement("td");
    const titleLink = document.createElement("a");
    titleLink.href = `/student/issue.html?id=${item.issue_id}`;
    titleLink.style.fontWeight = "600";
    titleLink.textContent = item.title;
    tdTitle.appendChild(titleLink);
    tr.appendChild(tdTitle);

    // Category
    const tdCat = document.createElement("td");
    tdCat.textContent = item.category;
    tr.appendChild(tdCat);

    // Location
    const tdLoc = document.createElement("td");
    tdLoc.textContent = item.room ? `${item.block} - ${item.room}` : item.block;
    tr.appendChild(tdLoc);

    // Priority
    const tdPrio = document.createElement("td");
    tdPrio.appendChild(createPriorityBadge(item.priority));
    tr.appendChild(tdPrio);

    // Status
    const tdStat = document.createElement("td");
    tdStat.appendChild(createStatusBadge(item.status));
    tr.appendChild(tdStat);

    // Date
    const tdDate = document.createElement("td");
    tdDate.textContent = formatDate(item.created_at);
    tr.appendChild(tdDate);

    tbody.appendChild(tr);
  });

  tableWrapper.appendChild(table);
  container.appendChild(tableWrapper);
}

// --- MY REPORTS PAGE ---
async function initMyReports() {
  if (!auth.requireAuth(["student"])) return;

  const urlParams = new URLSearchParams(window.location.search);
  const createdId = urlParams.get("created");
  if (createdId) {
    showToast(`Issue #${createdId} submitted successfully!`, "success");
  }

  const filterSelect = document.getElementById("status-filter");
  if (filterSelect) {
    filterSelect.addEventListener("change", () => {
      loadMyReports(filterSelect.value);
    });
  }

  await loadMyReports("");
}

async function loadMyReports(statusFilter = "") {
  const container = document.getElementById("my-reports-container");
  container.innerHTML = '<div style="padding: 2rem; text-align: center;"><span class="spinner"></span> Loading your reports...</div>';

  try {
    const url = statusFilter ? `/issues/mine?status=${encodeURIComponent(statusFilter)}` : "/issues/mine";
    const issues = await api.get(url);

    container.innerHTML = "";

    if (issues.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📋</div>
          <h3 style="font-size: 1.1rem; color: #fff; margin-bottom: 0.5rem;">No Issues Found</h3>
          <p style="margin-bottom: 1.5rem; font-size: 0.9rem;">
            ${statusFilter ? `No issues currently marked as "${statusFilter}".` : "You have not submitted any complaints yet."}
          </p>
          <a href="/student/report.html" class="btn btn-primary">➕ Report a Problem</a>
        </div>
      `;
      return;
    }

    const grid = document.createElement("div");
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = "repeat(auto-fill, minmax(320px, 1fr))";
    grid.style.gap = "1.25rem";

    issues.forEach((item) => {
      const card = document.createElement("div");
      card.className = "card";
      card.style.display = "flex";
      card.style.flexDirection = "column";
      card.style.cursor = "pointer";
      card.style.transition = "transform 0.15s ease, border-color 0.15s ease";

      card.addEventListener("mouseenter", () => {
        card.style.transform = "translateY(-2px)";
        card.style.borderColor = "var(--border-focus)";
      });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "translateY(0)";
        card.style.borderColor = "var(--border-color)";
      });

      card.addEventListener("click", () => {
        window.location.href = `/student/issue.html?id=${item.issue_id}`;
      });

      // Top badges row
      const topRow = document.createElement("div");
      topRow.style.display = "flex";
      topRow.style.justifyContent = "space-between";
      topRow.style.alignItems = "center";
      topRow.style.marginBottom = "0.75rem";

      const leftBadges = document.createElement("div");
      leftBadges.style.display = "flex";
      leftBadges.style.gap = "0.5rem";
      leftBadges.appendChild(createStatusBadge(item.status));
      leftBadges.appendChild(createPriorityBadge(item.priority));
      topRow.appendChild(leftBadges);

      const supportSpan = document.createElement("span");
      supportSpan.style.fontSize = "0.75rem";
      supportSpan.style.color = "var(--text-muted)";
      supportSpan.textContent = `👍 ${item.support_count}`;
      topRow.appendChild(supportSpan);

      card.appendChild(topRow);

      // Title
      const h3 = document.createElement("h3");
      h3.style.fontSize = "1.05rem";
      h3.style.marginBottom = "0.5rem";
      h3.style.color = "#fff";
      h3.textContent = item.title;
      card.appendChild(h3);

      // Description snippet
      const pDesc = document.createElement("p");
      pDesc.style.fontSize = "0.875rem";
      pDesc.style.color = "var(--text-sub)";
      pDesc.style.marginBottom = "1rem";
      pDesc.style.flex = "1";
      pDesc.style.display = "-webkit-box";
      pDesc.style.webkitLineClamp = "2";
      pDesc.style.webkitBoxOrient = "vertical";
      pDesc.style.overflow = "hidden";
      pDesc.textContent = item.description;
      card.appendChild(pDesc);

      // Assigned staff display if assigned
      if (item.assigned_staff_name) {
        const staffRow = document.createElement("div");
        staffRow.style.fontSize = "0.8rem";
        staffRow.style.color = "#c084fc";
        staffRow.style.marginBottom = "0.5rem";
        staffRow.style.display = "flex";
        staffRow.style.alignItems = "center";
        staffRow.style.gap = "0.35rem";
        staffRow.textContent = `👷 ${item.assigned_staff_name} (${item.assigned_staff_team || "Maintenance"})`;
        card.appendChild(staffRow);
      }

      // Location & Category
      const metaRow = document.createElement("div");
      metaRow.style.fontSize = "0.8rem";
      metaRow.style.color = "var(--text-muted)";
      metaRow.style.display = "flex";
      metaRow.style.justifyContent = "space-between";
      metaRow.style.paddingTop = "0.75rem";
      metaRow.style.borderTop = "1px solid var(--border-color)";

      const locSpan = document.createElement("span");
      locSpan.textContent = `📍 ${item.room ? `${item.block}, ${item.room}` : item.block}`;
      metaRow.appendChild(locSpan);

      const dateSpan = document.createElement("span");
      dateSpan.textContent = formatDate(item.created_at);
      metaRow.appendChild(dateSpan);

      card.appendChild(metaRow);
      grid.appendChild(card);
    });

    container.appendChild(grid);
  } catch (err) {
    console.error("Failed to load my reports:", err);
    container.innerHTML = `<div class="card" style="color: #ef4444; padding: 2rem; text-align: center;">Error: ${err.message}</div>`;
  }
}

// --- ISSUE DETAIL PAGE ---
async function initIssueDetail() {
  if (!auth.requireAuth(["student", "admin", "staff"])) return;

  const user = api.getUser();
  const backLink = document.querySelector('a[href="/student/my-reports.html"]');
  if (backLink && user) {
    if (user.role === "staff") {
      backLink.href = "/staff/tasks.html";
      backLink.textContent = "← Back to My Tasks";
    } else if (user.role === "admin") {
      backLink.href = "/admin/dashboard.html";
      backLink.textContent = "← Back to Operations Dashboard";
    }
  }

  const urlParams = new URLSearchParams(window.location.search);
  const issueId = urlParams.get("id");

  if (!issueId) {
    window.location.href = "/student/my-reports.html";
    return;
  }

  await loadIssueDetails(issueId);
  setupCommentSubmission(issueId);
}

async function loadIssueDetails(issueId) {
  try {
    const issue = await api.get(`/issues/${issueId}`);
    renderIssueDetails(issue);
  } catch (err) {
    console.error("Failed to load issue:", err);
    const container = document.getElementById("issue-detail-card");
    if (container) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: #ef4444;">
          <h2 style="margin-bottom: 0.5rem;">Access Denied or Not Found</h2>
          <p style="color: var(--text-muted); margin-bottom: 1.5rem;">${err.message || "You are not authorized to view this ticket."}</p>
          <a href="/student/my-reports.html" class="btn btn-outline">Return to My Reports</a>
        </div>
      `;
    }
  }
}

function renderIssueDetails(issue) {
  // Title & ID
  document.getElementById("detail-id").textContent = `#${issue.issue_id}`;
  document.getElementById("detail-title").textContent = issue.title;

  // Badges
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

  // Location
  const locParts = [issue.block];
  if (issue.building) locParts.push(issue.building);
  if (issue.room) locParts.push(issue.room);
  document.getElementById("detail-location").textContent = locParts.join(" / ");

  // Metadata
  document.getElementById("detail-reporter").textContent = issue.reporter_name;
  document.getElementById("detail-created").textContent = formatDate(issue.created_at);
  document.getElementById("detail-support-count").textContent = issue.support_count;

  // Assigned Technician
  const staffEl = document.getElementById("detail-assigned-staff");
  if (staffEl) {
    if (issue.assignment && issue.assignment.staff_name) {
      staffEl.textContent = `👷 ${issue.assignment.staff_name} (${issue.assignment.staff_team || "Maintenance"})`;
      staffEl.style.color = "#c084fc";
    } else {
      staffEl.textContent = "Pending Assignment";
      staffEl.style.color = "var(--text-muted)";
    }
  }

  // Photo
  const photoContainer = document.getElementById("detail-photo-container");
  if (issue.image_url) {
    photoContainer.style.display = "block";
    const imgEl = document.getElementById("detail-photo");
    imgEl.src = issue.image_url;
  } else {
    photoContainer.style.display = "none";
  }

  // Render Status Stepper Timeline
  renderStatusStepper(issue.status, issue.status_history);

  // Render Comments
  renderComments(issue.comments);
}

function renderStatusStepper(currentStatus, history) {
  const steps = ["Open", "Assigned", "In Progress", "Resolved"];
  const currentIdx = steps.indexOf(currentStatus);

  const container = document.getElementById("stepper-container");
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
    circle.style.width = "32px";
    circle.style.height = "32px";
    circle.style.borderRadius = "50%";
    circle.style.display = "flex";
    circle.style.alignItems = "center";
    circle.style.justifyContent = "center";
    circle.style.fontSize = "0.8rem";
    circle.style.fontWeight = "700";
    circle.style.marginBottom = "0.4rem";

    if (isCurrent) {
      circle.style.background = "var(--primary)";
      circle.style.color = "#fff";
      circle.style.boxShadow = "0 0 12px var(--primary-glow)";
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
    label.style.fontSize = "0.75rem";
    label.style.fontWeight = isCurrent ? "700" : "500";
    label.style.color = isCompleted ? "#fff" : "var(--text-muted)";
    label.textContent = stepName;

    stepItem.appendChild(circle);
    stepItem.appendChild(label);
    stepper.appendChild(stepItem);
  });

  container.appendChild(stepper);

  // History timeline log list
  const historyList = document.getElementById("history-list");
  historyList.innerHTML = "";

  if (history && history.length > 0) {
    history.forEach((h) => {
      const row = document.createElement("div");
      row.style.fontSize = "0.85rem";
      row.style.padding = "0.4rem 0";
      row.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
      row.style.display = "flex";
      row.style.justifyContent = "space-between";

      const left = document.createElement("span");
      const strong = document.createElement("strong");
      strong.textContent = h.new_status;
      left.appendChild(strong);
      left.appendChild(document.createTextNode(` by ${h.changed_by_name || "System"}`));
      row.appendChild(left);

      const right = document.createElement("span");
      right.style.color = "var(--text-muted)";
      right.textContent = formatDate(h.changed_at);
      row.appendChild(right);

      historyList.appendChild(row);
    });
  }
}

function renderComments(comments) {
  const container = document.getElementById("comments-list");
  container.innerHTML = "";

  if (!comments || comments.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem;">No comments yet. Have more information? Post below.</p>';
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
    authorSpan.textContent = `${c.user_name} (${c.user_role})`;
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

function setupCommentSubmission(issueId) {
  const form = document.getElementById("comment-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("comment-input");
    const text = input.value.trim();
    if (!text) return;

    const btn = document.getElementById("btn-add-comment");
    btn.disabled = true;

    try {
      await api.post(`/issues/${issueId}/comments`, { comment: text });
      input.value = "";
      showToast("Comment posted successfully!", "success");
      // Refresh details
      await loadIssueDetails(issueId);
    } catch (err) {
      showToast(err.message || "Failed to post comment.", "error");
    } finally {
      btn.disabled = false;
    }
  });
}
