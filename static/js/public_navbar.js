document.addEventListener("DOMContentLoaded", () => {
    const navbar = document.querySelector(".custom-navbar");
    const dropdowns = document.querySelectorAll(".dropdown");

    // Scroll effect: navbar moves to center when scrolling down
    window.addEventListener("scroll", () => {
        if (window.scrollY > 50) {
            navbar.classList.add("navbar-centered");
        } else {
            navbar.classList.remove("navbar-centered");
        }
    });

    // Dropdown hover for desktop
    dropdowns.forEach((dropdown) => {
        const toggle = dropdown.querySelector(".dropdown-toggle");
        const menu = dropdown.querySelector(".dropdown-menu");

        // Show dropdown on hover
        dropdown.addEventListener("mouseenter", () => {
            dropdown.classList.add("show");
            menu.classList.add("show");
        });

        dropdown.addEventListener("mouseleave", () => {
            dropdown.classList.remove("show");
            menu.classList.remove("show");
        });

        // Show/hide dropdown on click for mobile
        toggle.addEventListener("click", (e) => {
            e.preventDefault();
            dropdown.classList.toggle("show");
            menu.classList.toggle("show");
        });
    });

    // Optional: Close dropdowns if clicking outside
    document.addEventListener("click", (e) => {
        dropdowns.forEach((dropdown) => {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove("show");
                dropdown.querySelector(".dropdown-menu").classList.remove("show");
            }
        });
    });
});
