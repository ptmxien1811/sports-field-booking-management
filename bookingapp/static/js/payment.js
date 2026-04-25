// ===== PAYMENT.JS — Xử lý thanh toán =====

document.addEventListener("DOMContentLoaded", function () {
    const btnPay = document.getElementById("btn-pay");
    if (!btnPay) return;

    btnPay.addEventListener("click", function () {
        const bookingId = btnPay.getAttribute("data-booking-id");
        const paymentMethod = document.getElementById("payment-method").value;

        // Xác nhận trước khi thanh toán
        if (!confirm("Bạn có chắc chắn muốn thanh toán?")) return;

        // Vô hiệu hóa nút để tránh bấm 2 lần
        btnPay.disabled = true;
        btnPay.textContent = "Đang xử lý...";

        fetch("/api/payment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                booking_id: parseInt(bookingId),
                payment_method: paymentMethod
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.ok) {
                // Đổi thông báo trên nút
                btnPay.style.backgroundColor = "#218838";
                btnPay.textContent = "Thành công! Mã HĐ: #" + data.bill_id;
                
                // Trở về trang chủ sau 3 giây để người dùng kịp đọc thông báo
                setTimeout(() => {
                    window.location.href = "/";
                }, 3000);
            } else {
                alert("Lỗi: " + data.msg);
                btnPay.disabled = false;
                btnPay.textContent = "THANH TOÁN";
            }
        })
        .catch(err => {
            alert("Có lỗi xảy ra, vui lòng thử lại!");
            btnPay.disabled = false;
            btnPay.textContent = "THANH TOÁN";
        });
    });
});
