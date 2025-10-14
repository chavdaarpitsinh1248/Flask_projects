document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("theme-toggle");
    const nav = document.getElementById("main-nav");
    const body = document.body;

    // Exit early if body is missing (unlikely) or toggle button doesn't exist
    if (!body) return;

    const saved = localStorage.getItem("theme") || "light";

    // Apply theme safely
    if (saved === "dark") enableDark(false);
    else enableLight(false);

    // Only add event listener if toggle button exists
    if (btn) {
        btn.addEventListener("click", () => {
            if (body.classList.contains("bg-dark")) enableLight(true);
            else enableDark(true);
        });
    }

    function enableDark(save = true) {
        body.classList.add("bg-dark", "text-light");
        body.classList.remove("bg-light", "text-dark");

        if (nav) {
            nav.classList.remove("navbar-light", "bg-light");
            nav.classList.add("navbar-dark", "bg-dark");
        }

        if (btn) {
            btn.classList.remove("btn-outline-secondary");
            btn.classList.add("btn-outline-light");
            btn.textContent = "☀️";
        }

        if (save) localStorage.setItem("theme", "dark");
    }

    function enableLight(save = true) {
        body.classList.remove("bg-dark", "text-light");
        body.classList.add("bg-light", "text-dark");

        if (nav) {
            nav.classList.remove("navbar-dark", "bg-dark");
            nav.classList.add("navbar-light", "bg-light");
        }

        if (btn) {
            btn.classList.remove("btn-outline-light");
            btn.classList.add("btn-outline-secondary");
            btn.textContent = "🌙";
        }

        if (save) localStorage.setItem("theme", "light");
    }
});
