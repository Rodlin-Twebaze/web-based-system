document.addEventListener("DOMContentLoaded", () => {
    const user = requireSession();
    if (!user) return;

    document.getElementById("submittingAs").textContent = `${user.name} (${user.email})`;

    const form = document.getElementById("complaintForm");
    const errorBox = document.getElementById("complaintError");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        errorBox.textContent = "";

        const complaintType = document.getElementById("complaintCategory").value;
        const message = document.getElementById("complaint").value.trim();

        try {
            const result = await apiRequest("/complaints", {
                method: "POST",
                body: JSON.stringify({
                    created_by_user_id: user.id,
                    complaint_type: complaintType,
                    message,
                }),
            });

            const complaint = result.complaint;
            const params = new URLSearchParams({
                id: complaint.id,
                type: complaint.complaint_type,
                status: complaint.status,
            });
            window.location.href = `successful.html?${params.toString()}`;
        } catch (err) {
            const reason = err.message || "An unexpected error occurred.";
            window.location.href = `complaint-failed.html?reason=${encodeURIComponent(reason)}`;
        }
    });
});
