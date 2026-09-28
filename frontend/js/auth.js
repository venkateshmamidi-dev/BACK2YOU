/**
 * Back2You - Authentication & Session Management
 */

const Auth = {
    getToken() {
        return localStorage.getItem("back2you_token");
    },
    getUser() {
        const raw = localStorage.getItem("back2you_user");
        try { return raw ? JSON.parse(raw) : null; } catch { return null; }
    },
    isLoggedIn() {
        return !!this.getToken();
    },
    isAdmin() {
        const u = this.getUser();
        return u && (u.role === "ADMIN" || u.role === "MODERATOR");
    },
    setSession(token, user) {
        localStorage.setItem("back2you_token", token);
        localStorage.setItem("back2you_user", JSON.stringify(user));
    },
    clearSession() {
        localStorage.removeItem("back2you_token");
        localStorage.removeItem("back2you_user");
    },
    logout() {
        this.clearSession();
        window.location.href = "index.html";
    },
    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = "login.html";
            return false;
        }
        return true;
    },
    requireAdmin() {
        if (!this.isAdmin()) {
            window.location.href = "dashboard.html";
            return false;
        }
        return true;
    }
};

// Toast utility
function showToast(message, type = "default") {
    const container = document.getElementById("toast-container") || (() => {
        const c = document.createElement("div");
        c.id = "toast-container";
        c.className = "toast-container";
        document.body.appendChild(c);
        return c;
    })();

    const toast = document.createElement("div");
    toast.className = "toast";
    const colors = { success: "#16A34A", error: "#DC2626", info: "#2563EB", default: "#111827" };
    toast.style.borderLeft = `4px solid ${colors[type] || colors.default}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3800);
}

// Render nav based on auth state
function renderNav() {
    const user = Auth.getUser();
    const loggedIn = Auth.isLoggedIn();
    const isAdmin = Auth.isAdmin();

    const authLinksEl = document.getElementById("nav-auth-links");
    const userLinksEl = document.getElementById("nav-user-links");
    const adminLinkEl = document.getElementById("nav-admin-link");
    const userNameEl = document.getElementById("nav-user-name");
    const notifBadgeEl = document.getElementById("notif-badge");

    if (loggedIn) {
        if (authLinksEl) authLinksEl.style.display = "none";
        if (userLinksEl) userLinksEl.style.display = "flex";
        if (userNameEl && user) userNameEl.textContent = user.name.split(" ")[0];
        if (adminLinkEl) adminLinkEl.style.display = isAdmin ? "list-item" : "none";

        // Load unread notification count
        if (notifBadgeEl) {
            API.getNotifications(5).then(notifs => {
                const unread = notifs.filter(n => !n.is_read).length;
                if (unread > 0) {
                    notifBadgeEl.textContent = unread;
                    notifBadgeEl.style.display = "flex";
                }
            }).catch(() => {});
        }
    } else {
        if (authLinksEl) authLinksEl.style.display = "flex";
        if (userLinksEl) userLinksEl.style.display = "none";
    }

    // Mobile menu toggle
    const toggle = document.getElementById("mobile-menu-toggle");
    const navLinks = document.getElementById("nav-links-list");
    if (toggle && navLinks) {
        toggle.addEventListener("click", () => navLinks.classList.toggle("open"));
    }

    // Logout
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        Auth.logout();
    });
}

document.addEventListener("DOMContentLoaded", renderNav);
