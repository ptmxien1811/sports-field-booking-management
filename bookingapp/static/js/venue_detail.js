/* venue_detail.js – Booking nhiều khung giờ + Review */

const card        = document.querySelector(".vd-booking-card");
const PRODUCT_ID  = card ? parseInt(card.dataset.productId) : window.PRODUCT_ID;
const PRICE_HOUR  = card ? parseFloat(card.dataset.price)   : (window.PRICE_PER_HOUR || 0);

let selectedDate       = null;   // "YYYY-MM-DD"
let selectedSlots      = new Set(); // Set các label đã chọn: "HH:MM - HH:MM"
let currentYear, currentMonth;
let bookingsTodayCount = 0;
let selectedRating     = 0;

// ─── KHỞI TẠO ──────────────────────────────────────────────────────────────
(function init() {
    const now = new Date();
    currentYear  = now.getFullYear();
    currentMonth = now.getMonth();   // 0-based

    selectedDate = toDateStr(now);
    renderCalendar();
    fetchSlots(selectedDate);
})();


// ─── CALENDAR ──────────────────────────────────────────────────────────────
function renderCalendar() {
    const monthLabel = document.getElementById("monthLabel");
    const daysGrid   = document.getElementById("daysGrid");
    if (!monthLabel || !daysGrid) return;

    const months = ["Tháng 1","Tháng 2","Tháng 3","Tháng 4","Tháng 5","Tháng 6",
                    "Tháng 7","Tháng 8","Tháng 9","Tháng 10","Tháng 11","Tháng 12"];
    monthLabel.textContent = `${months[currentMonth]} ${currentYear}`;

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInM  = new Date(currentYear, currentMonth + 1, 0).getDate();
    const today    = new Date(); today.setHours(0, 0, 0, 0);
    const offset   = (firstDay + 6) % 7; // Mon=0

    daysGrid.innerHTML = "";

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
    const picked = new Date(dateStr);
    const today  = new Date(); today.setHours(0, 0, 0, 0);
    if (picked < today) return;

    selectedDate  = dateStr;
    selectedSlots.clear(); // Reset slots khi đổi ngày
    renderCalendar();
    fetchSlots(dateStr);
    updateBookingSummary();
}

function toDateStr(d) {
    const y   = d.getFullYear();
    const m   = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}


// ─── FETCH SLOTS ───────────────────────────────────────────────────────────
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
        el.textContent = `⚠️ Bạn đã đặt ${count}/${max} sân khác nhau trong ngày này (đã đạt giới hạn).`;
    } else if (count > 0) {
        el.style.display = "block";
        el.textContent = `ℹ️ Bạn đã đặt ${count}/${max} sân khác nhau ngày này. Mỗi sân vẫn đặt được nhiều giờ.`;

    } else {
        el.style.display = "none";
    }
}


// ─── RENDER SLOTS (hỗ trợ multi-select) ────────────────────────────────────
function renderSlots(slotsData, dateStr) {
    ["morning", "afternoon", "evening"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = "";
    });

    const nowDate = new Date();
    const selDate = new Date(dateStr);
    const isToday = selDate.toDateString() === nowDate.toDateString();

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
            let attrs = "";

            if (s.booked) {
                cls += " booked";
                attrs = 'disabled';
            } else if (isPast) {
                cls += " past";
                attrs = 'disabled';
            } else {
                // Nếu đang trong danh sách selected → highlight
                if (selectedSlots.has(s.label)) {
                    cls += " selected";
                }
                attrs = `onclick="toggleSlot(this, '${s.label}')"`;
            }

            container.insertAdjacentHTML("beforeend",
                `<div class="${cls}" ${attrs}>${s.label}</div>`);
        });
    });
}

// ─── TOGGLE SLOT (multi-select) ─────────────────────────────────────────────
function toggleSlot(el, label) {
    if (!window.IS_LOGGED_IN) { requireLogin(); return; }

    if (selectedSlots.has(label)) {
        // Bỏ chọn
        selectedSlots.delete(label);
        el.classList.remove("selected");
    }else {
        // Thêm vào
        selectedSlots.add(label);
        el.classList.add("selected");
    }

    updateBookingSummary();
    showBookMsg("", "");
}

// ─── CẬP NHẬT SUMMARY ───────────────────────────────────────────────────────
function updateBookingSummary() {
    const summary   = document.getElementById("bookingSummary");
    const tagsWrap  = document.getElementById("selectedSlotTags");
    const totalEl   = document.getElementById("totalPriceText");

    if (!summary) return;

    if (selectedSlots.size === 0) {
        summary.style.display = "none";
        return;
    }
toggleSlot
    summary.style.display = "block";

    // Render tags
    const sorted = Array.from(selectedSlots).sort();
    tagsWrap.innerHTML = '<div class="vd-slot-tags">' +
        sorted.map(label =>
            `<span class="vd-slot-tag">
                ${label}
                <span class="remove-slot" onclick="removeSlot('${label}')">×</span>
            </span>`
        ).join("") +
    '</div>';

    // Tổng tiền
    const total = selectedSlots.size * PRICE_HOUR;
    totalEl.textContent = `Tổng: ${total.toLocaleString("vi-VN")}đ (${selectedSlots.size} giờ)`;
}

// Xóa 1 slot từ tag
function removeSlot(label) {
    selectedSlots.delete(label);
    // Bỏ class selected trên DOM
    document.querySelectorAll(".slot").forEach(el => {
        if (el.textContent.trim() === label) {
            el.classList.remove("selected");
        }
    });
    updateBookingSummary();
}


// ─── ĐẶT SÂN ────────────────────────────────────────────────────────────────
const bookBtn = document.getElementById("bookBtn");
if (bookBtn) {
    bookBtn.addEventListener("click", () => {
        if (!window.IS_LOGGED_IN) { requireLogin(); return; }

        if (!selectedDate) {
            showBookMsg("Vui lòng chọn ngày.", "error");
            return;
        }

        if (selectedSlots.size === 0) {
            showBookMsg("Vui lòng chọn ít nhất 1 khung giờ.", "error");
            return;
        }

        const picked = new Date(selectedDate);
        const today  = new Date(); today.setHours(0, 0, 0, 0);
        if (picked < today) {
            showBookMsg("Không thể đặt sân ngày trong quá khứ.", "error");
            return;
        }

        bookBtn.disabled    = true;
        bookBtn.textContent = "Đang xử lý...";

        fetch("/api/book", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_id: PRODUCT_ID,
                slots:      Array.from(selectedSlots),  // Gửi nhiều slots
                date:       selectedDate,
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                showBookMsg("✅ " + data.msg, "success");
                selectedSlots.clear();
                updateBookingSummary();
                fetchSlots(selectedDate); // Reload slots
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


// ─── REVIEW ──────────────────────────────────────────────────────────────────
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
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ rating: selectedRating, content }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            setReviewMsg("✅ Đánh giá của bạn đã được ghi nhận!", "success");
            appendReviewCard(data);
            window.HAS_REVIEWED = true;
            document.getElementById("reviewForm").style.display = "none";
            const cnt = document.getElementById("reviewCount");
            if (cnt) cnt.textContent = parseInt(cnt.textContent) + 1;
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