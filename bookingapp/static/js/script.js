document.addEventListener("DOMContentLoaded", () => {

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

document.addEventListener("DOMContentLoaded", function () {

    const timeBtns = document.querySelectorAll(".time-btn");
    const selectedTime = document.getElementById("selected-time");

    timeBtns.forEach(btn => {
        btn.addEventListener("click", function () {

            timeBtns.forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            selectedTime.value = this.innerText;
        });
    });

});
// ===== CALENDAR + SLOTS =====
const MONTHS_VI = [
    'Tháng 1','Tháng 2','Tháng 3','Tháng 4','Tháng 5','Tháng 6',
    'Tháng 7','Tháng 8','Tháng 9','Tháng 10','Tháng 11','Tháng 12'
];

const card = document.querySelector('.vd-booking-card');
const PRODUCT_ID = card ? card.dataset.productId : null;

let cur     = { y: new Date().getFullYear(), m: new Date().getMonth() };
let selDay  = new Date().getDate();
let selSlot = null;
let slotsData = {};


function fmtDate(y, m, d) {
    return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}


// ===== FETCH SLOTS TỪ API =====
async function fetchSlots() {
    if (!selDay || !PRODUCT_ID) return;

    const dateStr = fmtDate(cur.y, cur.m, selDay);
    const res     = await fetch(`/api/slots/${PRODUCT_ID}?date=${dateStr}`);
    const data    = await res.json();

    slotsData = data.slots || {};

    const availText = document.getElementById('availText');
    if (availText) {
        availText.textContent = `Còn ${data.available} khung giờ trống`;
    }

    selSlot = null;
    renderAllSlots();
}


// ===== RENDER CALENDAR =====
function renderCal() {
    const monthLabel = document.getElementById('monthLabel');
    if (monthLabel) {
        monthLabel.textContent = MONTHS_VI[cur.m] + ', ' + cur.y;
    }

    const grid = document.getElementById('daysGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const first  = new Date(cur.y, cur.m, 1).getDay();
    const offset = first === 0 ? 6 : first - 1;
    const total  = new Date(cur.y, cur.m + 1, 0).getDate();
    const prev   = new Date(cur.y, cur.m, 0).getDate();

    // Ô trống đầu tháng
    for (let i = 0; i < offset; i++) {
        const b = document.createElement('button');
        b.className   = 'day other';
        b.textContent = prev - offset + 1 + i;
        b.disabled    = true;
        grid.appendChild(b);
    }

    // Các ngày trong tháng
    for (let d = 1; d <= total; d++) {
        const dow = (offset + d - 1) % 7;
        const b   = document.createElement('button');

        let cls = 'day';
        if (dow >= 5)    cls += ' weekend';
        if (d === selDay) cls += ' selected';

        b.className   = cls;
        b.textContent = d;
        b.onclick = () => {
            selDay  = d;
            selSlot = null;
            renderCal();
            fetchSlots();
        };
        grid.appendChild(b);
    }

    // Ô trống cuối tháng
    const rem = 7 - (offset + total) % 7;
    if (rem < 7) {
        for (let i = 1; i <= rem; i++) {
            const b = document.createElement('button');
            b.className   = 'day other';
            b.textContent = i;
            b.disabled    = true;
            grid.appendChild(b);
        }
    }
}


// ===== RENDER TIME SLOTS =====
function renderSlots(id, period) {
    const wrap = document.getElementById(id);
    if (!wrap) return;
    wrap.innerHTML = '';

    const slots = slotsData[period] || [];

    if (!slots.length) {
        wrap.innerHTML = '<span style="font-size:12px;color:#aaa">Không có khung giờ</span>';
        return;
    }

    slots.forEach(s => {
        const b = document.createElement('button');

        let cls = 'slot';
        if (s.booked)                        cls += ' booked';
        if (!s.booked && s.label === selSlot) cls += ' selected';

        b.className   = cls;
        b.textContent = s.label;
        b.disabled    = s.booked;

        if (!s.booked) {
            b.onclick = () => {
                selSlot = s.label;
                renderAllSlots();
            };
        }
        wrap.appendChild(b);
    });
}

function renderAllSlots() {
    renderSlots('morning',   'morning');
    renderSlots('afternoon', 'afternoon');
    renderSlots('evening',   'evening');
}


// ===== CHUYỂN THÁNG =====
function changeMonth(d) {
    cur.m += d;
    if (cur.m < 0)  { cur.m = 11; cur.y--; }
    if (cur.m > 11) { cur.m = 0;  cur.y++; }
    selDay  = null;
    selSlot = null;
    renderCal();
}


// ===== HIỆN THÔNG BÁO =====
function showMsg(msg, color) {
    const el = document.getElementById('bookMsg');
    if (!el) return;
    el.textContent  = msg;
    el.style.color  = color;
    setTimeout(() => { el.textContent = ''; }, 4000);
}


// ===== ĐẶT SÂN =====
async function handleBooking() {
    if (!selDay || !selSlot) {
        showMsg('Vui lòng chọn ngày và khung giờ!', '#e53935');
        return;
    }

    const dateStr = fmtDate(cur.y, cur.m, selDay);

    const res = await fetch('/api/book', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
            product_id: PRODUCT_ID,
            slot:       selSlot,
            date:       dateStr
        })
    });

    const data = await res.json();

    if (data.ok) {
        showMsg(data.msg, '#1a73e8');
        fetchSlots();
    } else {
        showMsg(data.msg, '#e53935');
    }
}


// ===== REVIEW =====
let selRating = 5;

function toggleReviewForm() {
    const f = document.getElementById('reviewForm');
    if (!f) return;
    f.style.display = f.style.display === 'none' ? 'block' : 'none';
}

function setRating(val) {
    selRating = val;
    document.querySelectorAll('.star-opt').forEach((s, i) => {
        s.style.color = i < val ? '#f5a623' : '#ccc';
    });
}

async function submitReview() {
    const contentEl = document.getElementById('reviewContent');
    if (!contentEl) return;

    const content = contentEl.value.trim();
    if (!content) {
        alert('Vui lòng nhập nội dung đánh giá!');
        return;
    }

    const res = await fetch(`/api/review/${PRODUCT_ID}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ rating: selRating, content })
    });

    const data = await res.json();

    if (!data.ok) {
        alert(data.msg);
        return;
    }

    // Thêm review mới lên đầu danh sách
    const list = document.getElementById('reviewList');
    if (list) {
        const card = document.createElement('div');
        card.className = 'vd-review-card';
        card.innerHTML = `
            <div class="vd-avatar">${data.author[0]}</div>
            <div class="vd-review-body">
                <div class="vd-review-header">
                    <span class="vd-rv-name">${data.author}</span>
                    <span class="vd-rv-date">${data.date_str}</span>
                </div>
                <div class="vd-stars-sm" style="color:#f5a623">${data.stars}</div>
                <p class="vd-rv-text">${data.content}</p>
            </div>`;
        list.prepend(card);
    }

    contentEl.value = '';
    document.getElementById('reviewForm').style.display = 'none';
}


// ===== KHỞI TẠO =====
document.addEventListener('DOMContentLoaded', () => {

    // Calendar + Slots
    renderCal();
    fetchSlots();

    // Nút đặt sân
    const bookBtn = document.getElementById('bookBtn');
    if (bookBtn) {
        bookBtn.addEventListener('click', handleBooking);
    }

    // Mặc định 5 sao
    setRating(5);
});