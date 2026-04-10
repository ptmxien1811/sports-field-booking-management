document.addEventListener("DOMContentLoaded", () => {
    // === 1. KHAI BÁO BIẾN DÙNG CHUNG ===
    const tabs = document.querySelectorAll(".nav-tabs a");
    const contents = document.querySelectorAll(".tab-content");
    const searchInput = document.getElementById("search-input");
    const suggestionsBox = document.getElementById("suggestions");

    // === 2. HÀM KÍCH HOẠT TAB (Gộp logic xử lý & LocalStorage) ===
    function activateTab(targetId) {
        // Xóa active cũ
        tabs.forEach(t => t.classList.remove("active"));
        contents.forEach(c => c.classList.remove("active"));

        // Thêm active mới
        const targetTab = document.querySelector(`[data-target="${targetId}"]`);
        const targetContent = document.getElementById(targetId);

        if (targetTab && targetContent) {
            targetTab.classList.add("active");
            targetContent.classList.add("active");
            localStorage.setItem("currentTab", targetId);
        }
    }

    // Gán sự kiện Click cho Tab
    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = tab.dataset.target;
            activateTab(targetId);
        });
    });

    // Tự động mở lại tab cũ khi load trang
    const savedTab = localStorage.getItem("currentTab") || "venues";
    activateTab(savedTab);


    // === 3. XỬ LÝ TƯƠNG TÁC NÚT (Đặt sân & Yêu thích) ===
    document.querySelectorAll(".book-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            alert("Bạn đã chọn đặt lịch thành công!");
        });
    });

    document.querySelectorAll(".fav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            btn.classList.toggle("active");
        });
    });


    // === 4. TÌM KIẾM + GỢI Ý ===
    const venues = [
        "Sân bóng đá mini 7 người", "Sân tennis tiêu chuẩn", "Hồ bơi 25m",
        "Sân cầu lông tiêu chuẩn", "Sân bóng rổ ngoài trời", "Sân bóng chuyền",
        "Sân bóng bàn", "Sân pickleball hiện đại"
    ];

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const query = searchInput.value.toLowerCase();
            suggestionsBox.innerHTML = "";
            if (query) {
                const filtered = venues.filter(v => v.toLowerCase().startsWith(query));
                filtered.forEach(v => {
                    const li = document.createElement("li");
                    li.textContent = v;
                    li.onclick = () => {
                        searchInput.value = v;
                        suggestionsBox.style.display = "none";
                    };
                    suggestionsBox.appendChild(li);
                });
                suggestionsBox.style.display = filtered.length ? "block" : "none";
            } else {
                suggestionsBox.style.display = "none";
            }
        });
    }
});