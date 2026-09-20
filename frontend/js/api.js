/**
 * FixFlow API Client Helper
 * Handles JWT bearer authentication, JSON parsing, and unified error handling.
 */

const API_BASE = "/api";

const api = {
  getToken() {
    return localStorage.getItem("fixflow_token");
  },

  setToken(token) {
    localStorage.setItem("fixflow_token", token);
  },

  clearToken() {
    localStorage.removeItem("fixflow_token");
    localStorage.removeItem("fixflow_user");
  },

  getUser() {
    const raw = localStorage.getItem("fixflow_user");
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("fixflow_user", JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
    const headers = options.headers ? { ...options.headers } : {};

    const token = this.getToken();
    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // Handle unauthenticated 401: redirect to login if not already there
      if (response.status === 401 && !url.includes("/auth/login") && !url.includes("/auth/register")) {
        this.clearToken();
        if (!window.location.pathname.endsWith("index.html") && window.location.pathname !== "/") {
          window.location.href = "/index.html";
        }
        throw new Error("Session expired. Please log in again.");
      }

      // If empty response (204)
      if (response.status === 204) {
        return null;
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const errorMsg = data && data.detail ? data.detail : `Request failed with status ${response.status}`;
        const err = new Error(errorMsg);
        err.status = response.status;
        err.data = data;
        throw err;
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || "GET"} ${url}]:`, err);
      throw err;
    }
  },

  get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  },

  post(endpoint, body) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  postFormData(endpoint, formData) {
    return this.request(endpoint, {
      method: "POST",
      body: formData,
    });
  },

  patch(endpoint, body) {
    return this.request(endpoint, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  },
};

// Global Toast helper
window.showToast = function (message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
};
