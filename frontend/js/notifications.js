/**
 * FixFlow In-App Notifications Component
 * Automatically injects a notification bell with unread badge and dropdown into the navbar.
 * Renders all user text safely via textContent.
 */

const notificationsManager = {
  notifications: [],
  unreadCount: 0,
  isOpen: false,
  pollTimer: null,

  init() {
    // Only init if user is logged in
    const token = api.getToken();
    if (!token) return;

    this.mountBellUI();
    this.fetchNotifications();

    // Periodic background poll every 30s
    if (!this.pollTimer) {
      this.pollTimer = setInterval(() => {
        if (api.getToken()) {
          this.fetchNotifications();
        }
      }, 30000);
    }
  },

  mountBellUI() {
    const navUser = document.querySelector(".nav-user");
    if (!navUser || document.getElementById("fixflow-notif-wrapper")) return;

    // Create wrapper
    const wrapper = document.createElement("div");
    wrapper.className = "notif-wrapper";
    wrapper.id = "fixflow-notif-wrapper";
    wrapper.style.marginRight = "0.5rem";

    // Bell Button
    const bellBtn = document.createElement("button");
    bellBtn.type = "button";
    bellBtn.className = "notif-bell-btn";
    bellBtn.id = "btn-notif-bell";
    bellBtn.setAttribute("aria-label", "Notifications");
    bellBtn.textContent = "🔔";

    // Badge
    const badge = document.createElement("span");
    badge.className = "notif-badge";
    badge.id = "notif-unread-badge";
    badge.style.display = "none";
    badge.textContent = "0";
    bellBtn.appendChild(badge);

    // Dropdown Container
    const dropdown = document.createElement("div");
    dropdown.className = "notif-dropdown";
    dropdown.id = "notif-dropdown-menu";

    // Dropdown Header
    const header = document.createElement("div");
    header.className = "notif-header";

    const title = document.createElement("h4");
    title.textContent = "Notifications";
    header.appendChild(title);

    const markAllBtn = document.createElement("button");
    markAllBtn.type = "button";
    markAllBtn.className = "btn btn-outline btn-sm";
    markAllBtn.style.fontSize = "0.75rem";
    markAllBtn.style.padding = "0.2rem 0.5rem";
    markAllBtn.textContent = "Mark all read";
    markAllBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.markAllAsRead();
    });
    header.appendChild(markAllBtn);

    dropdown.appendChild(header);

    // Notifications List
    const list = document.createElement("div");
    list.className = "notif-list";
    list.id = "notif-items-list";
    dropdown.appendChild(list);

    wrapper.appendChild(bellBtn);
    wrapper.appendChild(dropdown);

    // Insert before the logout button in nav-user
    navUser.insertBefore(wrapper, navUser.firstChild);

    // Toggle dropdown on bell click
    bellBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });

    // Close dropdown on click outside
    document.addEventListener("click", (e) => {
      if (!wrapper.contains(e.target)) {
        this.closeDropdown();
      }
    });
  },

  async fetchNotifications() {
    try {
      const data = await api.get("/notifications");
      if (Array.isArray(data)) {
        this.notifications = data;
        this.unreadCount = data.filter((n) => !n.is_read).length;
        this.updateBadge();
        if (this.isOpen) {
          this.renderList();
        }
      }
    } catch (err) {
      console.warn("Could not fetch notifications:", err);
    }
  },

  updateBadge() {
    const badge = document.getElementById("notif-unread-badge");
    if (!badge) return;

    if (this.unreadCount > 0) {
      badge.textContent = this.unreadCount > 9 ? "9+" : String(this.unreadCount);
      badge.style.display = "flex";
    } else {
      badge.style.display = "none";
    }
  },

  toggleDropdown() {
    if (this.isOpen) {
      this.closeDropdown();
    } else {
      this.openDropdown();
    }
  },

  openDropdown() {
    const menu = document.getElementById("notif-dropdown-menu");
    if (!menu) return;
    this.isOpen = true;
    menu.style.display = "flex";
    this.renderList();
  },

  closeDropdown() {
    const menu = document.getElementById("notif-dropdown-menu");
    if (!menu) return;
    this.isOpen = false;
    menu.style.display = "none";
  },

  renderList() {
    const list = document.getElementById("notif-items-list");
    if (!list) return;

    list.innerHTML = "";

    if (this.notifications.length === 0) {
      const empty = document.createElement("div");
      empty.className = "notif-empty";
      empty.textContent = "No notifications yet.";
      list.appendChild(empty);
      return;
    }

    this.notifications.forEach((notif) => {
      const item = document.createElement("div");
      item.className = `notif-item ${notif.is_read ? "read" : "unread"}`;

      // Message text safely rendered with textContent
      const msg = document.createElement("div");
      msg.className = "notif-msg";
      msg.textContent = notif.message;
      item.appendChild(msg);

      // Timestamp
      const time = document.createElement("div");
      time.className = "notif-time";
      time.textContent = this.formatTime(notif.created_at);
      item.appendChild(time);

      // Click to mark as read
      item.addEventListener("click", async () => {
        if (!notif.is_read) {
          await this.markAsRead(notif.notification_id);
        }
      });

      list.appendChild(item);
    });
  },

  async markAsRead(notificationId) {
    try {
      await api.post(`/notifications/${notificationId}/read`);
      const target = this.notifications.find((n) => n.notification_id === notificationId);
      if (target) {
        target.is_read = true;
        this.unreadCount = Math.max(0, this.unreadCount - 1);
        this.updateBadge();
        this.renderList();
      }
    } catch (err) {
      console.warn("Failed to mark notification read:", err);
    }
  },

  async markAllAsRead() {
    try {
      await api.post("/notifications/read-all");
      this.notifications.forEach((n) => (n.is_read = true));
      this.unreadCount = 0;
      this.updateBadge();
      this.renderList();
    } catch (err) {
      console.warn("Failed to mark all notifications read:", err);
    }
  },

  formatTime(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diffSec = Math.floor((now - date) / 1000);

    if (diffSec < 60) return "Just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  },
};

// Auto-initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  notificationsManager.init();
});
