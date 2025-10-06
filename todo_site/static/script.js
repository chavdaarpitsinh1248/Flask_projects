const toggle = document.getElementById("toggle-dark");
const body = document.body;

// Load saved mode
if (localStorage.getItem("dark-mode") === "true") {
    body.classList.add("dark");
    toggle.checked = true;
}

toggle.addEventListener("change", () => {
    if (toggle.checked) {
        body.classList.add("dark");
        localStorage.setItem("dark-mode", "true");
    } else {
        body.classList.remove("dark");
        localStorage.setItem("dark-mode", "false");
    }
});
