document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("registerForm");
    const errorBox = document.getElementById("registerError");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        errorBox.textContent = "";

        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirmpassword").value;

        if (password !== confirmPassword) {
            errorBox.textContent = "Passwords do not match.";
            errorBox.hidden = false;
            return;
        }

        const payload = {
            name: document.getElementById("fullname").value.trim(),
            username: document.getElementById("username").value.trim(),
            email: document.getElementById("email").value.trim(),
            role: document.getElementById("usertype").value,
            password,
            confirm_password: confirmPassword,
        };

        try {
            await apiRequest("/auth/register", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            window.location.href = "login.html?registered=1";
        } catch (err) {
            errorBox.textContent = err.message || "Registration failed. Please try again.";
            errorBox.hidden = false;
        }
    });
});
