/* venue_detail.js – Booking + Review logic với đầy đủ ràng buộc */

const card       = document.querySelector(".vd-booking-card");
const PRODUCT_ID = card ? parseInt(card.dataset.productId) : window.PRODUCT_ID;

let selectedDate = null;   // "YYYY-MM-DD"
let selectedSlot = null;   // "HH:MM - HH:MM"
let currentYear, currentMonth;
let bookingsTodayCount = 0;  // số lần đã đặt trong ngày đang chọn
let selectedRating = 0;

// ─── Khởi tạo ──────────────────────────────────────────────────────────────
(function init() {
    const now = new Date();
    currentYear  = now.getFullYear();
    currentMonth = now.getMonth();   // 0-based

    // Chọn mặc định hôm nay
    const today = toDateStr(now);
    selectedDate = today;
    renderCalendar();
    fetchSlots(today);
})();


// ─── Calendar ──────────────────────────────────────────────────────────────
function renderCalendar() {
    const monthLabel = document.getElementById("monthLabel");
    const daysGrid   = document.getElementById("daysGrid");
    if (!monthLabel || !daysGrid) return;

    const months = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                    "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"];
    monthLabel.textContent = `${months[currentMonth]} ${currentYear}`;

    const firstDay  = new Date(currentYear, currentMonth, 1).getDay(); // 0=Sun
    const daysInM   = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today     = new Date();
    today.setHours(0, 0, 0, 0);

    // Chuyển Sun=0 → Mon=0
    const offset = (firstDay + 6) % 7;

    daysGrid.innerHTML = "";

    // Ô trống đầu tháng
    for (let i = 0; i < offset; i++) {
        daysGrid.insertAdjacentHTML("beforeend", `<div class="day"></div>`);
    }

    for (let d = 1; d <= daysInM; d++) {
        const date    = new Date(currentYear, currentMonth, d);
        const dateStr = toDateStr(date);
        const isPast  = date < today;
        const isToday = date.getTime() === today.getTime();
        const isSel   = dateStr === selectedDate;

        let cls = "day";
        if (isPast)  cls += " past";
        if (isToday) cls += " today";
        if (isSel)   cls += " selected";

        const onclick = isPast ? "" : `onclick="selectDate('${dateStr}')"`;
        daysGrid.insertAdjacentHTML("beforeend",
            `<div class="${cls}" ${onclick}>${d}</div>`);
    }
}

function changeMonth(dir) {
    currentMonth += dir;
    if (currentMonth < 0)  { currentMonth = 11; currentYear--; }
    if (currentMonth > 11) { currentMonth = 0;  currentYear++; }
    renderCalendar();
}

function selectDate(dateStr) {
    // Không cho chọn ngày quá khứ
    const picked = new Date(dateStr);
    const today  = new Date(); today.setHours(0,0,0,0);
    if (picked < today) return;

    selectedDate = dateStr;
    selectedSlot = null;
    renderCalendar();
    fetchSlots(dateStr);
}

function toDateStr(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}


// ─── Fetch slots từ server ──────────────────────────────────────────────────
function fetchSlots(dateStr) {
    setAvailText("Đang tải...");
    fetch(`/api/slots/${PRODUCT_ID}?date=${dateStr}`)
        .then(r => r.json())
        .then(data => {
            bookingsTodayCount = data.bookings_today || 0;
            renderSlots(data.slots, dateStr);
            setAvailText(data.available > 0
                ? `🟢 Còn ${data.available} khung giờ trống`
                : "🔴 Hết chỗ ngày này");
            updateDailyLimitInfo(bookingsTodayCount, data.max_per_day || 3);
        })
        .catch(() => setAvailText("Không thể tải dữ liệu"));
}

function setAvailText(txt) {
    const el = document.getElementById("availText");
    if (el) el.textContent = txt;
}

function updateDailyLimitInfo(count, max) {
    const el = document.getElementById("dailyLimitInfo");
    if (!el) return;
    if (!window.IS_LOGGED_IN) { el.style.display = "none"; return; }
    if (count >= max) {
        el.style.display = "block";
        el.textContent   = `⚠️ Bạn đã đặt ${count}/${max} sân trong ngày này (đã đạt giới hạn).`;
    } else if (count > 0) {
        el.style.display = "block";
        el.textContent   = `ℹ️ Bạn đã đặt ${count}/${max} sân ngày này.`;
    } else {
        el.style.display = "none";
    }
}


// ─── Render time slots ──────────────────────────────────────────────────────
function renderSlots(slotsData, dateStr) {
    const periodMap = { morning: "morning", afternoon: "afternoon", evening: "evening" };
    Object.values(periodMap).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = "";
    });

    const nowDate  = new Date();
    const selDate  = new Date(dateStr);
    const isToday  = selDate.toDateString() === nowDate.toDateString();

    Object.entries(slotsData).forEach(([period, slots]) => {
        const container = document.getElementById(period);
        if (!container) return;

        slots.forEach(s => {
            const startStr = s.label.split(" - ")[0];
            const [sh, sm] = startStr.split(":").map(Number);

            let isPast = false;
            if (isToday) {
                const slotTime = new Date(selDate);
                slotTime.setHours(sh, sm, 0, 0);
                isPast = slotTime <= nowDate;
            }

            let cls = "slot";
            let onclick = "";

            if (s.booked) {
                cls += " booked";
            } else if (isPast) {
                cls += " past";
            } else if (s.label === selectedSlot) {
                cls += " selected";
            } else {
                onclick = `onclick="selectSlot(this, '${s.label}')"`;
            }

            container.insertAdjacentHTML("beforeend",
                `<div class="${cls}" ${onclick}>${s.label}</div>`);
        });
    });
}

function selectSlot(el, label) {
    // Nếu chưa đăng nhập, chặn luôn
    if (!window.IS_LOGGED_IN) {
        requireLogin();
        return;
    }
    // Nếu đã đạt giới hạn
    if (bookingsTodayCount >= 3) {
        showBookMsg("⚠️ Bạn đã đặt tối đa 3 sân trong ngày này.", "error");
        return;
    }

    document.querySelectorAll(".slot.selected").forEach(s => s.classList.remove("selected"));
    el.classList.add("selected");
    selectedSlot = label;
    showBookMsg("", "");
}


// ─── Đặt sân ───────────────────────────────────────────────────────────────
const bookBtn = document.getElementById("bookBtn");
if (bookBtn) {
    bookBtn.addEventListener("click", () => {
        if (!window.IS_LOGGED_IN) { requireLogin(); return; }
        if (!selectedDate || !selectedSlot) {
            showBookMsg("Vui lòng chọn ngày và khung giờ.", "error");
            return;
        }

        // Client-side: kiểm tra ngày quá khứ
        const picked = new Date(selectedDate);
        const today  = new Date(); today.setHours(0,0,0,0);
        if (picked < today) {
            showBookMsg("Không thể đặt sân ngày trong quá khứ.", "error");
            return;
        }

        // Client-side: kiểm tra giới hạn 3 sân/ngày
        if (bookingsTodayCount >= 3) {
            showBookMsg("Bạn đã đặt tối đa 3 sân trong ngày này.", "error");
            return;
        }

        bookBtn.disabled     = true;
        bookBtn.textContent  = "Đang xử lý...";

        fetch("/api/book", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_id: PRODUCT_ID,
                slot:       selectedSlot,
                date:       selectedDate,
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                showBookMsg("✅ " + data.msg, "success");
                // Refresh slots để hiển thị slot vừa đặt
                selectedSlot = null;
                fetchSlots(selectedDate);
            } else {
                showBookMsg("❌ " + data.msg, "error");
            }
        })
        .catch(() => showBookMsg("❌ Có lỗi xảy ra. Vui lòng thử lại.", "error"))
        .finally(() => {
            bookBtn.disabled    = false;
            bookBtn.textContent = "Đặt sân ngay";
        });
    });
}

function showBookMsg(msg, type) {
    const el = document.getElementById("bookMsg");
    if (!el) return;
    el.textContent = msg;
    el.style.color = type === "success" ? "#2e7d32"
                   : type === "error"   ? "#c62828"
                   : "#555";
}


// ─── Review ─────────────────────────────────────────────────────────────────
function toggleReviewForm() {
    const form = document.getElementById("reviewForm");
    if (!form) return;
    form.style.display = form.style.display === "none" ? "block" : "none";
}

function requireLogin() {
    alert("Vui lòng đăng nhập để thực hiện tính năng này.");
    window.location.href = "/login";
}

function setRating(val) {
    selectedRating = val;
    const stars = document.querySelectorAll(".star-opt");
    stars.forEach(s => {
        s.classList.toggle("active", parseInt(s.dataset.val) <= val);
    });
    const hint = document.getElementById("ratingHint");
    const labels = ["", "Tệ", "Không tốt", "Bình thường", "Tốt", "Xuất sắc"];
    if (hint) hint.textContent = `${val} sao – ${labels[val]}`;
}

function submitReview() {
    if (!window.IS_LOGGED_IN) { requireLogin(); return; }
    if (!window.CAN_REVIEW) {
        setReviewMsg("❌ Chỉ người đã đặt sân mới được đánh giá.", "error");
        return;
    }
    if (window.HAS_REVIEWED) {
        setReviewMsg("❌ Bạn đã đánh giá sân này rồi.", "error");
        return;
    }
    if (selectedRating === 0) {
        setReviewMsg("Vui lòng chọn số sao (1–5).", "error");
        return;
    }

    const content = (document.getElementById("reviewContent")?.value || "").trim();
    if (!content) {
        setReviewMsg("Vui lòng nhập nội dung đánh giá.", "error");
        return;
    }

    fetch(`/api/review/${PRODUCT_ID}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating: selectedRating, content }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            setReviewMsg("✅ Đánh giá của bạn đã được ghi nhận!", "success");
            appendReviewCard(data);
            // Ẩn form và cập nhật trạng thái
            window.HAS_REVIEWED = true;
            document.getElementById("reviewForm").style.display = "none";
            // Cập nhật số lượng & avg rating
            const cnt = document.getElementById("reviewCount");
            if (cnt) cnt.textContent = parseInt(cnt.textContent) + 1;
            // Reload avg (đơn giản: reload trang sau 1.5s)
            setTimeout(() => location.reload(), 1500);
        } else {
            setReviewMsg("❌ " + data.msg, "error");
        }
    })
    .catch(() => setReviewMsg("❌ Lỗi kết nối.", "error"));
}

function setReviewMsg(msg, type) {
    const el = document.getElementById("reviewMsg");
    if (!el) return;
    el.textContent = msg;
    el.style.color = type === "success" ? "#2e7d32" : "#c62828";
}

function appendReviewCard(data) {
    const list = document.getElementById("reviewList");
    if (!list) return;
    const initials = (data.author || "?")[0].toUpperCase();
    const card = document.createElement("div");
    card.className = "vd-review-card";
    card.innerHTML = `
        <div class="vd-avatar">${initials}</div>
        <div class="vd-review-body">
            <div class="vd-review-header">
                <span class="vd-rv-name">${data.author}</span>
                <span class="vd-rv-date">Hôm nay</span>
            </div>
            <div class="vd-stars-sm" style="color:#f5a623">${data.stars}</div>
            <p class="vd-rv-text">${data.content}</p>
        </div>`;
    list.prepend(card);
}