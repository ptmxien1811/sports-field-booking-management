
document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".nav-tabs a");
    const contents = document.querySelectorAll(".tab-content");

    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();

            // Xóa active ở tất cả các tab và nội dung
            tabs.forEach(t => t.classList.remove("active"));
            contents.forEach(c => c.classList.remove("active"));

            // Thêm active cho tab vừa click
            tab.classList.add("active");

            // Hiển thị nội dung tương ứng
            const target = tab.getAttribute("data-target"); // Dùng getAttribute cho chắc chắn
            const el = document.getElementById(target);
            if (el) {
                el.classList.add("active");
            }
        });
    });
});