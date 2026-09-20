/**
 * FixFlow Campus Operations Analytics Controller
 * Fetches analytics APIs and renders Chart.js visualizations, hotspots, and heatmap matrix.
 */

let categoryChartInstance = null;
let blockChartInstance = null;
let trendChartInstance = null;
let statusChartInstance = null;

// Distinct harmonious palette for categories
const CATEGORY_COLORS = {
  Equipment: "#6366f1",
  Electrical: "#f59e0b",
  Plumbing: "#06b6d4",
  Cleaning: "#10b981",
  Furniture: "#8b5cf6",
  Internet: "#3b82f6",
  "Doors/Windows": "#ec4899",
  Other: "#94a3b8",
};

const DEFAULT_CHART_COLORS = [
  "#6366f1",
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ec4899",
  "#8b5cf6",
  "#06b6d4",
  "#64748b",
];

document.addEventListener("DOMContentLoaded", async () => {
  // Ensure user is authenticated admin
  if (!auth.requireAuth(["admin"])) return;

  const user = api.getUser();
  if (user) {
    const greeting = document.getElementById("user-greeting");
    if (greeting) greeting.textContent = `Admin: ${user.name}`;
  }

  // Load all analytics modules
  await loadAllAnalytics();
});

async function loadAllAnalytics() {
  const refreshBtn = document.getElementById("btn-refresh-analytics");
  if (refreshBtn) {
    refreshBtn.disabled = true;
    refreshBtn.textContent = "Loading...";
  }

  try {
    // Fetch all analytics datasets in parallel
    const [
      summary,
      byCategory,
      byBlock,
      byStatus,
      trend,
      hotspots,
      heatmap,
      resTime,
    ] = await Promise.all([
      api.get("/analytics/summary"),
      api.get("/analytics/by-category"),
      api.get("/analytics/by-block"),
      api.get("/analytics/by-status"),
      api.get("/analytics/trend?days=30"),
      api.get("/analytics/hotspots?limit=8"),
      api.get("/analytics/heatmap"),
      api.get("/analytics/resolution-time"),
    ]);

    // 1. Metric Summary Cards
    renderSummaryCards(summary, resTime);

    // 2. Charts
    renderCategoryChart(byCategory);
    renderBlockChart(byBlock);
    renderTrendChart(trend);
    renderStatusChart(byStatus);

    // 3. Hotspots & Heatmap
    renderHotspots(hotspots);
    renderHeatmap(heatmap);
  } catch (err) {
    console.error("Failed to load analytics:", err);
    showToast("Failed to load analytics: " + (err.message || "Unknown error"), "error");
  } finally {
    if (refreshBtn) {
      refreshBtn.disabled = false;
      refreshBtn.textContent = "🔄 Refresh Data";
    }
  }
}

function renderSummaryCards(summary, resTime) {
  if (summary) {
    document.getElementById("stat-total").textContent = summary.total ?? 0;
    document.getElementById("stat-open").textContent = summary.open ?? 0;
    document.getElementById("stat-in-progress").textContent = summary.in_progress ?? 0;
    document.getElementById("stat-resolved").textContent = summary.resolved ?? 0;
  }

  const avgEl = document.getElementById("stat-avg-res-time");
  const metaEl = document.getElementById("stat-res-meta");
  if (resTime && resTime.resolved_count > 0) {
    avgEl.textContent = `${resTime.average_hours} hrs`;
    let metaText = `${resTime.resolved_count} resolved tickets`;
    if (resTime.fastest_hours !== null && resTime.slowest_hours !== null) {
      metaText += ` (Fastest: ${resTime.fastest_hours}h, Max: ${resTime.slowest_hours}h)`;
    }
    metaEl.textContent = metaText;
  } else {
    avgEl.textContent = "N/A";
    metaEl.textContent = "No resolved tickets yet";
  }
}

function renderCategoryChart(data) {
  const canvas = document.getElementById("categoryChart");
  const emptyEl = document.getElementById("category-empty");
  if (!canvas) return;

  if (!data || data.length === 0) {
    canvas.style.display = "none";
    emptyEl.style.display = "block";
    return;
  }
  canvas.style.display = "block";
  emptyEl.style.display = "none";

  if (categoryChartInstance) categoryChartInstance.destroy();

  const labels = data.map((d) => d.category);
  const counts = data.map((d) => d.count);
  const backgroundColors = labels.map(
    (cat, i) => CATEGORY_COLORS[cat] || DEFAULT_CHART_COLORS[i % DEFAULT_CHART_COLORS.length]
  );

  categoryChartInstance = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: counts,
          backgroundColor: backgroundColors,
          borderColor: "#1e293b",
          borderWidth: 2,
          hoverOffset: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "65%",
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: "#cbd5e1",
            font: { family: "Inter", size: 12 },
            boxWidth: 14,
            padding: 12,
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw} issues`,
          },
        },
      },
    },
  });
}

function renderBlockChart(data) {
  const canvas = document.getElementById("blockChart");
  const emptyEl = document.getElementById("block-empty");
  if (!canvas) return;

  if (!data || data.length === 0) {
    canvas.style.display = "none";
    emptyEl.style.display = "block";
    return;
  }
  canvas.style.display = "block";
  emptyEl.style.display = "none";

  if (blockChartInstance) blockChartInstance.destroy();

  const labels = data.map((d) => d.block);
  const counts = data.map((d) => d.count);
  const colors = ["#4f46e5", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

  blockChartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Reported Issues",
          data: counts,
          backgroundColor: labels.map((_, i) => colors[i % colors.length]),
          borderRadius: 6,
          maxBarThickness: 45,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.raw} issues in ${ctx.label}`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { family: "Inter" } },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            precision: 0,
            font: { family: "Inter" },
          },
        },
      },
    },
  });
}

function renderTrendChart(data) {
  const canvas = document.getElementById("trendChart");
  const emptyEl = document.getElementById("trend-empty");
  if (!canvas) return;

  if (!data || data.length === 0) {
    canvas.style.display = "none";
    emptyEl.style.display = "block";
    return;
  }
  canvas.style.display = "block";
  emptyEl.style.display = "none";

  if (trendChartInstance) trendChartInstance.destroy();

  // Shorten date label to MM-DD
  const labels = data.map((d) => {
    const parts = d.date.split("-");
    return parts.length === 3 ? `${parts[1]}/${parts[2]}` : d.date;
  });
  const counts = data.map((d) => d.count);

  const ctx = canvas.getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, "rgba(245, 158, 11, 0.35)");
  gradient.addColorStop(1, "rgba(245, 158, 11, 0.0)");

  trendChartInstance = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "New Issues",
          data: counts,
          borderColor: "#f59e0b",
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointBackgroundColor: "#f59e0b",
          pointBorderColor: "#1e293b",
          pointBorderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.raw} issues created`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            maxTicksLimit: 10,
            font: { family: "Inter", size: 11 },
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            precision: 0,
            font: { family: "Inter" },
          },
        },
      },
    },
  });
}

function renderStatusChart(data) {
  const canvas = document.getElementById("statusChart");
  const emptyEl = document.getElementById("status-empty");
  if (!canvas) return;

  if (!data || data.length === 0) {
    canvas.style.display = "none";
    emptyEl.style.display = "block";
    return;
  }
  canvas.style.display = "block";
  emptyEl.style.display = "none";

  if (statusChartInstance) statusChartInstance.destroy();

  const statusColors = {
    Open: "#3b82f6",
    Assigned: "#8b5cf6",
    "In Progress": "#f59e0b",
    Resolved: "#10b981",
  };

  const labels = data.map((d) => d.status);
  const counts = data.map((d) => d.count);
  const bgColors = labels.map((s) => statusColors[s] || "#94a3b8");

  statusChartInstance = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: counts,
          backgroundColor: bgColors,
          borderColor: "#1e293b",
          borderWidth: 2,
          hoverOffset: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "60%",
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: "#cbd5e1",
            font: { family: "Inter", size: 12 },
            boxWidth: 14,
            padding: 12,
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${ctx.raw} issues`,
          },
        },
      },
    },
  });
}

function renderHotspots(hotspots) {
  const container = document.getElementById("hotspots-list");
  if (!container) return;

  if (!hotspots || hotspots.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 1.5rem; color: var(--text-muted); font-size: 0.9rem;">
        No recurring location hotspots found. All reported issues are evenly distributed.
      </div>
    `;
    return;
  }

  container.innerHTML = "";

  hotspots.forEach((spot, idx) => {
    const item = document.createElement("div");
    item.className = "hotspot-item";

    const left = document.createElement("div");
    left.style.display = "flex";
    left.style.alignItems = "center";
    left.style.gap = "0.75rem";

    const rankBadge = document.createElement("span");
    rankBadge.className = "badge";
    rankBadge.style.background = idx === 0 ? "#ef4444" : "rgba(255, 255, 255, 0.08)";
    rankBadge.style.color = idx === 0 ? "#fff" : "var(--text-muted)";
    rankBadge.style.fontWeight = "700";
    rankBadge.textContent = `#${idx + 1}`;
    left.appendChild(rankBadge);

    const info = document.createElement("div");

    const title = document.createElement("div");
    title.style.fontWeight = "600";
    title.style.color = "#fff";
    title.style.fontSize = "0.95rem";
    title.textContent = `${spot.block} — ${spot.room}`;
    info.appendChild(title);

    left.appendChild(info);
    item.appendChild(left);

    const right = document.createElement("div");
    right.style.display = "flex";
    right.style.alignItems = "center";
    right.style.gap = "0.5rem";

    const countBadge = document.createElement("span");
    countBadge.className = "badge";
    countBadge.style.background = spot.count > 1 ? "rgba(239, 68, 68, 0.2)" : "rgba(148, 163, 184, 0.15)";
    countBadge.style.color = spot.count > 1 ? "#f87171" : "var(--text-muted)";
    countBadge.style.border = spot.count > 1 ? "1px solid rgba(239, 68, 68, 0.4)" : "1px solid var(--border-color)";
    countBadge.textContent = `${spot.count} reported issue${spot.count > 1 ? "s" : ""}`;
    right.appendChild(countBadge);

    item.appendChild(right);
    container.appendChild(item);
  });
}

function renderHeatmap(heatmapData) {
  const container = document.getElementById("heatmap-container");
  if (!container) return;

  if (!heatmapData || !heatmapData.blocks || heatmapData.blocks.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
        No heatmap data available.
      </div>
    `;
    return;
  }

  const { blocks, categories, matrix, max_count } = heatmapData;

  const table = document.createElement("table");
  table.className = "heatmap-table";

  // Header row
  const thead = document.createElement("thead");
  const headerTr = document.createElement("tr");

  const cornerTh = document.createElement("th");
  cornerTh.textContent = "Campus Block";
  headerTr.appendChild(cornerTh);

  categories.forEach((cat) => {
    const th = document.createElement("th");
    th.textContent = cat;
    headerTr.appendChild(th);
  });
  thead.appendChild(headerTr);
  table.appendChild(thead);

  // Body rows
  const tbody = document.createElement("tbody");
  blocks.forEach((blk) => {
    const tr = document.createElement("tr");

    const rowLabel = document.createElement("td");
    rowLabel.className = "row-label";
    rowLabel.textContent = blk;
    tr.appendChild(rowLabel);

    categories.forEach((cat) => {
      const td = document.createElement("td");
      const count = (matrix[blk] && matrix[blk][cat]) || 0;
      td.textContent = count;

      if (count > 0) {
        // Calculate heat intensity
        const intensity = max_count > 0 ? count / max_count : 0.5;
        const alpha = Math.max(0.18, Math.min(0.85, intensity));
        td.style.background = `rgba(99, 102, 241, ${alpha})`;
        td.style.color = alpha > 0.5 ? "#ffffff" : "#c7d2fe";
        td.title = `${blk} • ${cat}: ${count} issue(s)`;
      } else {
        td.style.background = "rgba(15, 23, 42, 0.4)";
        td.style.color = "rgba(148, 163, 184, 0.4)";
        td.title = `${blk} • ${cat}: 0 issues`;
      }

      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.innerHTML = "";
  container.appendChild(table);
}
