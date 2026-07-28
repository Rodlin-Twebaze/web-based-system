document.addEventListener("DOMContentLoaded", async () => {
    const admin = requireSession("admin");
    if (!admin) return;

    document.getElementById("welcomeName").textContent = admin.name;

    const allBody = document.getElementById("allComplaintsBody");
    const allEmptyState = document.getElementById("allEmptyState");
    const myBody = document.getElementById("myComplaintsBody");
    const myEmptyState = document.getElementById("myEmptyState");

    try {
        const context = await loadAdminContext();
        const allComplaints = await fetchComplaints();

        renderComplaintsTable(allBody, allEmptyState, allComplaints, context);

        const assignedToMe = allComplaints.filter((c) => c.assigned_to_user_id === admin.id);
        renderComplaintsTable(myBody, myEmptyState, assignedToMe, context);
    } catch (err) {
        allEmptyState.textContent = err.message || "Failed to load complaints.";
        allEmptyState.hidden = false;
    }
});
