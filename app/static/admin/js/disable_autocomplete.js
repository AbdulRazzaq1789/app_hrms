document.addEventListener("DOMContentLoaded", function () {
    // find all inputs that look like date fields
    document.querySelectorAll("input").forEach(function (el) {
        if (
            el.name.includes("date") ||
            el.classList.contains("vDateField") ||
            el.classList.contains("jalali_date-date")
        ) {
            el.setAttribute("autocomplete", "off");
            el.setAttribute("autocorrect", "off");
            el.setAttribute("autocapitalize", "off");
            el.setAttribute("spellcheck", "false");
        }
    });
});
