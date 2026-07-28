document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const errorBox = document.getElementById("loginError");
    const infoBox = document.getElementById("loginInfo");

    const params = new URLSearchParams(window.location.search);
    if (params.get("registered") === "1") {
        infoBox.textContent = "Registration successful. Please log in below.";
        infoBox.hidden = false;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.hidden = true;
        errorBox.innerHTML = "";

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        try {
            const result = await apiRequest("/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password }),
            });

            saveSession(result.user);
            window.location.href =
                result.user.role === "admin" ? "admin-dashboard.html" : "user-dashboard.html";
        } catch (err) {
            if (err.status === 401) {
                errorBox.innerHTML =
                    "You don't have an account with these details. <a href=\"register.html\">Register here</a>.";
            } else {
                errorBox.textContent = err.message || "Login failed. Please try again.";
            }
            errorBox.hidden = false;
        }
    });
});
