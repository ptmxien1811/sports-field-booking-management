
/**
 * HÀM KHỞI TẠO CHÍNH - Chạy khi trang tải xong
 */
document.addEventListener("DOMContentLoaded", function () {
    //  1. KHỞI TẠO TÍNH NĂNG ĐIỀU HƯỚNG TAB
    initNavigationTabs();

    //  2. KHỞI TẠO TÍNH NĂNG TÌM KIẾM
    initSearchAndSuggestions();

    // 3. KHỞI TẠO LỊCH VÀ KHUNG GIỜ (TRANG CHI TIẾT)
    initBookingSystem();

    // 4. KHỞI TẠO THÔNG BÁO TỪ HỆ THỐNG
    initSystemAlerts();

    //  5. THIẾT LẬP MẶC ĐỊNH ĐÁNH GIÁ
    setRating(5);
});

/**
 * QUẢN LÝ TAB VÀ LƯU TRẠNG THÁI
 */
function initNavigationTabs() {
    const tabs = document.querySelectorAll(".nav-tabs a");
    const contents = document.querySelectorAll(".tab-content");

    function activateTab(targetId) {
        tabs.forEach(t => t.classList.remove("active"));
        contents.forEach(c => c.classList.remove("active"));

        const targetTab = document.querySelector(`[data-target="${targetId}"]`);
        const targetContent = document.getElementById(targetId);

        if (targetTab && targetContent) {
            targetTab.classList.add("active");
            targetContent.classList.add("active");
            localStorage.setItem("currentTab", targetId);
        }
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            activateTab(tab.dataset.target);
        });
    });

    const savedTab = localStorage.getItem("currentTab") || "venues";
    activateTab(savedTab);
}

/**
 * QUẢN LÝ TÌM KIẾM VÀ GỢI Ý
 */
function initSearchAndSuggestions() {
    const searchInput = document.getElementById("search-input");
    const suggestionsBox = document.getElementById("suggestions");
    const searchBtn = document.getElementById('search-btn');
    const allCards = document.querySelectorAll("div.venue-card");

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
                const filtered = venues.filter(v => v.toLowerCase().includes(query));
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
    }

    if (searchBtn) {
        searchBtn.addEventListener("click", () => {
            const query = searchInput.value.toLowerCase().trim();
            if (query) {
                let found = false;
                allCards.forEach(card => {
                    const nameTag = card.querySelector("h3");
                    if (nameTag && nameTag.textContent.toLowerCase().includes(query)) {
                        card.style.display = "block";
                        found = true;
                    } else {
                        card.style.display = "none";
                    }
                });
                if (!found) {
                    alert("Không tìm thấy sân: " + query);
                    allCards.forEach(c => c.style.display = "block");
                }
            } else {
                allCards.forEach(card => card.style.display = "block");
            }
        });
    }
}

/**
 * HỆ THỐNG ĐẶT SÂN (LỊCH & SLOTS)
 */
function initBookingSystem() {
    const bookBtn = document.getElementById('bookBtn');
    if (bookBtn) {
        bookBtn.addEventListener('click', handleBooking);
    }

    // Nếu có container lịch thì mới render
    if (document.getElementById('daysGrid')) {
        renderCal();
        fetchSlots();
    }
}

/**
 * XỬ LÝ THÔNG BÁO FLASH TỪ FLASK
 */
function initSystemAlerts() {
    const messageElements = document.querySelectorAll('#flask-messages .flash-data');
    messageElements.forEach(el => {
        const msg = el.textContent.trim();
        if (msg) alert(msg);
    });

    const container = document.getElementById('flask-messages');
    if (container) container.innerHTML = '';
}

/**
 * CÁC HÀM XỬ LÝ LỌC NÂNG CAO (Gọi trực tiếp từ HTML)
 */
function applyAdvancedFilter() {
    const selectedCats = Array.from(document.querySelectorAll('.filter-category:checked')).map(cb => cb.value.toLowerCase());
    const priceRadio = document.querySelector('input[name="priceRange"]:checked');
    const selectedAmens = Array.from(document.querySelectorAll('.filter-amenity:checked')).map(cb => cb.value.toLowerCase());
    const activeTabContent = document.querySelector('.tab-content.active');
    const allCards = document.querySelectorAll('.venue-card');

    allCards.forEach(card => {
        const cardName = card.querySelector('h3').textContent.toLowerCase();
        const priceText = card.querySelector('.product-price')?.textContent || "0";
        const cardPrice = parseInt(priceText.replace(/\D/g, ''));
        const cardAmens = card.querySelector('.hidden-amenities')?.textContent.toLowerCase() || "";

        let isMatch = true;
        if (selectedCats.length > 0 && !selectedCats.some(cat => cardName.includes(cat))) isMatch = false;
        if (isMatch && priceRadio) {
            const [min, max] = priceRadio.value.split('-').map(Number);
            if (cardPrice < min || cardPrice > max) isMatch = false;
        }
        if (isMatch && selectedAmens.length > 0) {
            if (!selectedAmens.every(amen => cardAmens.includes(amen))) isMatch = false;
        }
        card.style.display = isMatch ? 'block' : 'none';
    });

    const modal = bootstrap.Modal.getInstance(document.getElementById('filterModal'));
    if (modal) modal.hide();
}

function resetFilters() {
    const filterForm = document.getElementById('advanced-filter-form');
    if (filterForm) filterForm.reset();
    document.querySelectorAll('.venue-card').forEach(card => card.style.display = 'block');
}

/**
 * LOGIC LỊCH VÀ KHUNG GIỜ (CORE)
 */
const MONTHS_VI = ['Tháng 1','Tháng 2','Tháng 3','Tháng 4','Tháng 5','Tháng 6','Tháng 7','Tháng 8','Tháng 9','Tháng 10','Tháng 11','Tháng 12'];
const cardBooking = document.querySelector('.vd-booking-card');
const PRODUCT_ID = cardBooking ? cardBooking.dataset.productId : null;

let cur = { y: new Date().getFullYear(), m: new Date().getMonth() };
let selDay = new Date().getDate();
let selSlot = null;
let slotsData = {};

function fmtDate(y, m, d) { return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`; }

async function fetchSlots() {
    if (!selDay || !PRODUCT_ID) return;
    const dateStr = fmtDate(cur.y, cur.m, selDay);
    const res = await fetch(`/api/slots/${PRODUCT_ID}?date=${dateStr}`);
    const data = await res.json();
    slotsData = data.slots || {};
    const availText = document.getElementById('availText');
    if (availText) availText.textContent = `Còn ${data.available} khung giờ trống`;
    selSlot = null;
    renderAllSlots();
}

function renderCal() {
    const monthLabel = document.getElementById('monthLabel');
    if (monthLabel) monthLabel.textContent = MONTHS_VI[cur.m] + ', ' + cur.y;

    const grid = document.getElementById('daysGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const first = new Date(cur.y, cur.m, 1).getDay();
    const offset = first === 0 ? 6 : first - 1;
    const total = new Date(cur.y, cur.m + 1, 0).getDate();
    const prevMax = new Date(cur.y, cur.m, 0).getDate();

    for (let i = 0; i < offset; i++) {
        const b = document.createElement('button');
        b.className = 'day other'; b.textContent = prevMax - offset + 1 + i; b.disabled = true;
        grid.appendChild(b);
    }
    for (let d = 1; d <= total; d++) {
        const dow = (offset + d - 1) % 7;
        const b = document.createElement('button');
        b.className = `day ${dow >= 5 ? 'weekend' : ''} ${d === selDay ? 'selected' : ''}`;
        b.textContent = d;
        b.onclick = () => { selDay = d; selSlot = null; renderCal(); fetchSlots(); };
        grid.appendChild(b);
    }
}

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
        b.className = `slot ${s.booked ? 'booked' : ''} ${(!s.booked && s.label === selSlot) ? 'selected' : ''}`;
        b.textContent = s.label;
        b.disabled = s.booked;
        if (!s.booked) b.onclick = () => { selSlot = s.label; renderAllSlots(); };
        wrap.appendChild(b);
    });
}

function renderAllSlots() {
    renderSlots('morning', 'morning');
    renderSlots('afternoon', 'afternoon');
    renderSlots('evening', 'evening');
}

function changeMonth(d) {
    cur.m += d;
    if (cur.m < 0) { cur.m = 11; cur.y--; }
    else if (cur.m > 11) { cur.m = 0; cur.y++; }
    selDay = null; selSlot = null; renderCal();
}

function showMsg(msg, color) {
    const el = document.getElementById('bookMsg');
    if (el) { el.textContent = msg; el.style.color = color; setTimeout(() => { el.textContent = ''; }, 4000); }
}

async function handleBooking() {
    if (!selDay || !selSlot) { showMsg('Vui lòng chọn ngày và khung giờ!', '#e53935'); return; }
    const res = await fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: PRODUCT_ID, slot: selSlot, date: fmtDate(cur.y, cur.m, selDay) })
    });
    const data = await res.json();
    if (data.ok) { showMsg(data.msg, '#1a73e8'); fetchSlots(); }
    else { showMsg(data.msg, '#e53935'); }
}

/**
 * ĐÁNH GIÁ & YÊU THÍCH
 */
let selRating = 5;
function toggleReviewForm() {
    const f = document.getElementById('reviewForm');
    if (f) f.style.display = f.style.display === 'none' ? 'block' : 'none';
}

function setRating(val) {
    selRating = val;
    document.querySelectorAll('.star-opt').forEach((s, i) => {
        s.style.color = i < val ? '#f5a623' : '#ccc';
    });
}

async function submitReview() {
    const content = document.getElementById('reviewContent')?.value.trim();
    if (!content) return alert('Vui lòng nhập nội dung!');
    const res = await fetch(`/api/review/${PRODUCT_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: selRating, content })
    });
    const data = await res.json();
    if (!data.ok) return alert(data.msg);

    const list = document.getElementById('reviewList');
    if (list) {
        const card = document.createElement('div');
        card.className = 'vd-review-card';
        card.innerHTML = `<div class="vd-avatar">${data.author[0]}</div><div class="vd-review-body"><div class="vd-review-header"><span class="vd-rv-name">${data.author}</span><span class="vd-rv-date">${data.date_str}</span></div><div class="vd-stars-sm" style="color:#f5a623">${data.stars}</div><p class="vd-rv-text">${data.content}</p></div>`;
        list.prepend(card);
    }
    document.getElementById('reviewContent').value = ''; toggleReviewForm();
}



function toggleHeart(el, productId) {
    fetch(`/api/favorite/${productId}`, { method: 'POST' })
    .then(res => {
        if (res.status === 401) {
            alert("Vui lòng đăng nhập để thực hiện tính năng này!");
            window.location.href = "/login";
            return null;
        }
        if (res.status === 404) {
            console.warn("Sân không tồn tại:", productId);
            return null;
        }
        if (!res.ok) {
            return res.json().then(d => { console.error(d.msg); return null; });
        }
        return res.json();
    })
    .then(data => {
        if (!data || !data.ok) return;

        const allHeartBtns = document.querySelectorAll(`.fav-btn[onclick*="${productId}"]`);
        const favTab = document.getElementById('favorites');
        if (!favTab) return;

        let favListContainer = favTab.querySelector('.favorite-list');
        let emptyMsg = favTab.querySelector('.alert-info');

        if (data.added) {
            // --- THÊM VÀO YÊU THÍCH ---
            allHeartBtns.forEach(btn => {
                const icon = btn.querySelector('i');
                icon.classList.replace('fa-regular', 'fa-solid');
                icon.classList.add('text-danger');
            });

            if (!favListContainer) {
                favListContainer = document.createElement('div');
                favListContainer.className = 'favorite-list d-flex flex-wrap gap-3';
                favTab.appendChild(favListContainer);
            }

            const alreadyInFav = favListContainer.querySelector(`[data-product-id="${productId}"]`);
            if (!alreadyInFav) {
                const sourceCard = document.querySelector(`#venues .venue-card:has(.fav-btn[onclick*="${productId}"])`);
                if (sourceCard) {
                    const clone = sourceCard.cloneNode(true);
                    clone.setAttribute('data-product-id', productId);
                    const cloneFavBtn = clone.querySelector('.fav-btn');
                    if (cloneFavBtn) {
                        cloneFavBtn.onclick = function() { toggleHeart(this, productId); };
                    }
                    favListContainer.appendChild(clone);
                }
            }
            if (emptyMsg) emptyMsg.style.display = 'none';

        } else {
            // --- BỎ YÊU THÍCH ---
            allHeartBtns.forEach(btn => {
                const icon = btn.querySelector('i');
                icon.classList.replace('fa-solid', 'fa-regular');
                icon.classList.remove('text-danger');
            });

            const cardInFav = favTab.querySelector(`[data-product-id="${productId}"]`) ||
                              favTab.querySelector(`.venue-card:has(.fav-btn[onclick*="${productId}"])`);
            if (cardInFav) cardInFav.remove();

            const updatedContainer = favTab.querySelector('.favorite-list');

            if (!updatedContainer || updatedContainer.children.length === 0) {
                if (!emptyMsg) {
                    emptyMsg = document.createElement('div');
                    emptyMsg.className = 'alert alert-info';
                    emptyMsg.textContent = 'Bạn chưa có sân nào trong danh sách yêu thích.';
                    favTab.appendChild(emptyMsg);
                }
                emptyMsg.style.display = 'block';
                if (updatedContainer) updatedContainer.remove();
            }
        }
    })
    .catch(err => console.error("Lỗi đồng bộ:", err));
}