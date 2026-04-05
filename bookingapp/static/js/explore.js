// TAB chuyển nội dung
    const tabs = document.querySelectorAll(".nav-tabs a");
    const contents = document.querySelectorAll(".tab-content");

    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            contents.forEach(c => c.classList.remove("active"));
            const target = tab.dataset.target;
            const el = document.getElementById(target);
            if (el) el.classList.add("active");
        });
    });