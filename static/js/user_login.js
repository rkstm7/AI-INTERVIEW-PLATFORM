document.addEventListener("DOMContentLoaded", function () {
    // Fade Scroll Animation
    const leftFade = document.querySelectorAll(".fade-scroll-left");
    const rightFade = document.querySelectorAll(".fade-scroll-right");
    const options = { threshold: 0.2, rootMargin: "0px 0px -50px 0px" };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) entry.target.classList.add("visible");
            else entry.target.classList.remove("visible");
        });
    }, options);
    leftFade.forEach((el) => observer.observe(el));
    rightFade.forEach((el) => observer.observe(el));

    // Bootstrap Toast Initialization
    var toastElList = [].slice.call(document.querySelectorAll(".toast"));
    var toastList = toastElList.map(function (toastEl) {
        return new bootstrap.Toast(toastEl, { delay: 5000 });
    });
    toastList.forEach((toast) => toast.show());
});