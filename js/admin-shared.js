// Shared rendering/actions for the admin dashboard and the per-status
// (open/pending/closed) admin pages.

const STATUS_ORDER = { open: 0, pending: 1, closed: 2 };

async function fetchUsersMap() {
    const result = await apiRequest("/users");
    const map = {};
    (result.users || []).forEach((u) => {
        map[u.id] = u;
    });
    return map;
}

async function fetchAdminUsers() {
    const result = await apiRequest("/users?role=admin");
    return result.users || [];
}

async function fetchComplaints(query = "") {
    const result = await apiRequest(`/complaints${query}`);
    return result.complaints || [];
}

// Fetches the lookup data every row needs (all users, and admins for the
// assignment dropdown) once, so it can be reused across multiple tables.
async function loadAdminContext() {
    const [usersMap, adminUsers] = await Promise.all([fetchUsersMap(), fetchAdminUsers()]);
    return { usersMap, adminUsers };
}

function sortByStatus(complaints) {
    return [...complaints].sort(
        (a, b) => (STATUS_ORDER[a.status] ?? 99) - (STATUS_ORDER[b.status] ?? 99)
    );
}

async function updateComplaint(id, payload) {
    return apiRequest(`/complaints/${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
    });
}

function buildComplaintRow(complaint, context) {
    const { usersMap, adminUsers } = context;
    const tr = document.createElement("tr");
    tr.dataset.id = complaint.id;

    const creator = usersMap[complaint.created_by_user_id];

    const statusOptions = ["open", "pending", "closed"]
        .map(
            (s) =>
                `<option value="${s}" ${s === complaint.status ? "selected" : ""}>${s}</option>`
        )
        .join("");

    const assignOptions = ['<option value="">Unassigned</option>']
        .concat(
            adminUsers.map(
                (admin) =>
                    `<option value="${admin.id}" ${
                        admin.id === complaint.assigned_to_user_id ? "selected" : ""
                    }>${escapeHtml(admin.name)}</option>`
            )
        )
        .join("");

    tr.innerHTML = `
        <td>${escapeHtml(creator ? creator.name : "Unknown")}<br><small>${escapeHtml(
        creator ? creator.email : ""
    )}</small></td>
        <td>${escapeHtml(complaint.complaint_type)}</td>
        <td>${escapeHtml(complaint.message)}</td>
        <td><select class="status-select">${statusOptions}</select></td>
        <td><select class="assign-select">${assignOptions}</select></td>
        <td>${new Date(complaint.date_created).toLocaleDateString()}</td>
        <td><button type="button" class="btn btn-danger delete-btn">Delete</button></td>
    `;

    tr.querySelector(".status-select").addEventListener("change", async (event) => {
        try {
            await updateComplaint(complaint.id, { status: event.target.value });
            complaint.status = event.target.value;
        } catch (err) {
            alert(err.message || "Failed to update status.");
        }
    });

    tr.querySelector(".assign-select").addEventListener("change", async (event) => {
        const value = event.target.value || null;
        try {
            await updateComplaint(complaint.id, { assigned_to_user_id: value });
            complaint.assigned_to_user_id = value;
        } catch (err) {
            alert(err.message || "Failed to update assignment.");
        }
    });

    tr.querySelector(".delete-btn").addEventListener("click", async () => {
        if (!confirm("Delete this complaint? This cannot be undone.")) return;
        try {
            await apiRequest(`/complaints/${complaint.id}`, { method: "DELETE" });
            tr.remove();
        } catch (err) {
            alert(err.message || "Failed to delete complaint.");
        }
    });

    return tr;
}

function renderComplaintsTable(tbodyEl, emptyStateEl, complaints, context) {
    tbodyEl.innerHTML = "";
    if (complaints.length === 0) {
        if (emptyStateEl) emptyStateEl.hidden = false;
        return;
    }
    if (emptyStateEl) emptyStateEl.hidden = true;
    sortByStatus(complaints).forEach((complaint) => {
        tbodyEl.appendChild(buildComplaintRow(complaint, context));
    });
}

// Used by opening.html / pending.html / closed.html.
async function initStatusPage(status) {
    const admin = requireSession("admin");
    if (!admin) return;

    const tbody = document.getElementById("complaintsBody");
    const emptyState = document.getElementById("emptyState");

    try {
        const context = await loadAdminContext();
        const complaints = await fetchComplaints(`?status=${status}`);
        renderComplaintsTable(tbody, emptyState, complaints, context);
    } catch (err) {
        if (emptyState) {
            emptyState.textContent = err.message || "Failed to load complaints.";
            emptyState.hidden = false;
        }
    }
}
