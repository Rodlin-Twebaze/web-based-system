// Shared helpers used across the frontend pages: talking to the FastAPI
// backend, tracking the logged-in user client-side (no JWT/sessions on the
// server, so this is just enough state to drive the UI), and safe rendering.

const API_BASE = "http://localhost:8000";
const SESSION_KEY = "cms_user";

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    let data = null;
    try {
        data = await response.json();
    } catch (err) {
        data = null;
    }

    if (!response.ok) {
        const message = (data && data.detail) || "Request failed";
        const error = new Error(message);
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
}

function saveSession(user) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

function getSession() {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
}

function clearSession() {
    sessionStorage.removeItem(SESSION_KEY);
}

// Redirects to the login page (and returns null) if there's no logged-in
// user, or if a specific role was required and doesn't match.
function requireSession(requiredRole) {
    const user = getSession();
    if (!user || (requiredRole && user.role !== requiredRole)) {
        window.location.href = "login.html";
        return null;
    }
    return user;
}

// Escapes user-supplied text before it's dropped into innerHTML templates.
function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}
