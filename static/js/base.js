// Animate page load
document.addEventListener("DOMContentLoaded", function () {
    const wrapper = document.querySelector(".page-wrapper");
    wrapper.classList.add("visible");

    // Optional: handle link clicks for fade-out
    const links = document.querySelectorAll("a");
    links.forEach(link => {
        link.addEventListener("click", (e) => {
            // ignore external links or anchors
            if (link.target !== "_blank" && !link.href.includes("#")) {
                e.preventDefault();
                wrapper.classList.add("fade-out");
                setTimeout(() => {
                    window.location.href = link.href;
                }, 400); // match fade-out duration
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    var toastElList = [].slice.call(document.querySelectorAll('.toast'))
    toastElList.forEach(function (toastEl) {
        var toast = new bootstrap.Toast(toastEl, { delay: 4000 })
        toast.show()
    })
});