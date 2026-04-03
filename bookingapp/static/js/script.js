document.addEventListener("DOMContentLoaded", () => {
    // Nút đặt lịch
    document.querySelectorAll(".book-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            alert("Bạn đã chọn đặt lịch thành công!");
            const bookedList = document.querySelector("#booked-list");
            const card = btn.closest(".venue-card").cloneNode(true);
            bookedList.appendChild(card);
        });
    });

    // Toggle trái tim yêu thích
    document.querySelectorAll(".fav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            btn.classList.toggle("active");
            const favList = document.querySelector("#fav-list");
            const card = btn.closest(".venue-card").cloneNode(true);
            const name = card.querySelector("h3").textContent;

            if (btn.classList.contains("active")) {
                favList.appendChild(card);
            } else {
                document.querySelectorAll("#fav-list .venue-card").forEach(c => {
                    if (c.querySelector("h3").textContent === name) c.remove();
                });
            }
        });
    });

    // TAB chuyển nội dung
    const tabs = document.querySelectorAll(".nav-tabs a");
    const contents = document.querySelectorAll(".tab-content");

    tabs.forEach(tab => {
    tab.addEventListener("click", (e) => {
        e.preventDefault();

        // reset tab
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        // ẩn toàn bộ content
        contents.forEach(c => c.classList.remove("active"));

        // hiện đúng tab
        const target = tab.dataset.target;
        const el = document.getElementById(target);
        if (el) el.classList.add("active");
    });
});

    // TÌM KIẾM + GỢI Ý
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");
    const filterBtn = document.getElementById("filter-btn");
    const suggestionsBox = document.getElementById("suggestions");

    const venues = [
        "Sân bóng đá mini 7 người",
        "Sân tennis tiêu chuẩn",
        "Hồ bơi 25m",
        "Sân cầu lông tiêu chuẩn",
        "Sân bóng rổ ngoài trời",
        "Sân bóng chuyền",
        "Sân bóng bàn",
        "Sân pickleball hiện đại"
    ];

    searchInput.addEventListener("input", () => {
        const query = searchInput.value.toLowerCase();
        suggestionsBox.innerHTML = "";
        if (query) {
            const filtered = venues.filter(v => v.toLowerCase().startsWith(query));
            filtered.forEach(v => {
                const li = document.createElement("li");
                li.textContent = v;
                li.addEventListener("click", () => {
                    searchInput.value = v;
                    suggestionsBox.style.display = "none";
                });
                suggestionsBox.appendChild(li);
            });
            suggestionsBox.style.display = filtered.length ? "block" : "none";
        } else {
            suggestionsBox.style.display = "none";
        }
    });

    searchBtn.addEventListener("click", () => {
        const query = searchInput.value.trim();
        if (query) {
            alert("Bạn đang tìm: " + query);
        } else {
            alert("Vui lòng nhập từ khóa tìm kiếm!");
        }
    });
});
