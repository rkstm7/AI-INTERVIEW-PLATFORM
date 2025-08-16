document.addEventListener("DOMContentLoaded", () => {
    const el = document.querySelector(".typewriter");
    const text = el.dataset.text;
    const typingSpeed = 50; // ms per letter
    const holdTime = 7000;  // 7 seconds pause after typing
    let index = 0;
    let forward = true; // typing or deleting

    function typewriterLoop() {
        if (forward) {
            // typing forward
            if (index < text.length) {
                el.textContent += text.charAt(index);
                index++;
                setTimeout(typewriterLoop, typingSpeed);
            } else {
                forward = false; // start deleting after pause
                setTimeout(typewriterLoop, holdTime);
            }
        } else {
            // deleting backward
            if (index > 0) {
                el.textContent = text.substring(0, index - 1);
                index--;
                setTimeout(typewriterLoop, typingSpeed);
            } else {
                forward = true; // start typing again
                setTimeout(typewriterLoop, 500); // small pause before typing
            }
        }
    }

    typewriterLoop();
});