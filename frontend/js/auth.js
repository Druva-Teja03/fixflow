/**
 * FixFlow Authentication and Route Guards
 */

const auth = {
  redirectByRole(role) {
    if (role === "student") {
      window.location.href = "/student/dashboard.html";
    } else if (role === "admin") {
      window.location.href = "/admin/dashboard.html";
    } else if (role === "staff") {
      window.location.href = "/staff/tasks.html";
    } else {
      window.location.href = "/index.html";
    }
  },

  async login(email, password) {
    try {
      const response = await api.post("/auth/login", { email, password });
      api.setToken(response.access_token);
      api.setUser(response.user);
      return response.user;
    } catch (err) {
      throw err;
    }
  },

  async register(name, email, password) {
    try {
      const response = await api.post("/auth/register", { name, email, password });
      return response;
    } catch (err) {
      throw err;
    }
  },

  logout() {
    api.clearToken();
    window.location.href = "/index.html";
  },

  requireAuth(allowedRoles = []) {
    const token = api.getToken();
    const user = api.getUser();

    if (!token || !user) {
      this.logout();
      return false;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
      alert("Access Denied: You do not have permission to view this page.");
      this.redirectByRole(user.role);
      return false;
    }

    return true;
  },

  initNavUser() {
    const user = api.getUser();
    if (user) {
      const userNameEl = document.getElementById("nav-user-name");
      const userRoleEl = document.getElementById("nav-user-role");
      if (userNameEl) userNameEl.textContent = user.name;
      if (userRoleEl) userRoleEl.textContent = user.role;
    }
  }
};
