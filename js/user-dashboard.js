document.addEventListener("DOMContentLoaded", async () => {
    const user = requireSession();
    if (!user) return;

    document.getElementById("welcomeName").textContent = user.name;

    const tableBody = document.getElementById("complaintsBody");
    const emptyState = document.getElementById("emptyState");

    try {
        const result = await apiRequest(`/complaints?created_by_user_id=${encodeURIComponent(user.id)}`);
        const complaints = result.complaints || [];

        if (complaints.length === 0) {
            emptyState.hidden = false;
            return;
        }

        complaints
            .sort((a, b) => new Date(b.date_created) - new Date(a.date_created))
            .forEach((complaint) => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${escapeHtml(complaint.complaint_type)}</td>
                    <td>${escapeHtml(complaint.message)}</td>
                    <td><span class="status-badge status-${escapeHtml(complaint.status)}">${escapeHtml(complaint.status)}</span></td>
                    <td>${new Date(complaint.date_created).toLocaleDateString()}</td>
                `;
                tableBody.appendChild(row);
            });
    } catch (err) {
        emptyState.textContent = "Unable to load your complaints right now. Please try again later.";
        emptyState.hidden = false;
    }
});
