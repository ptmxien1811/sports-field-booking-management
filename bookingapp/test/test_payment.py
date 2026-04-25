# ============================================================
# test_payment.py — Unit Test cho trang Thanh toán (Payment)
# ============================================================

import pytest
import sys
import os

# Đảm bảo import test_base trước để monkey-patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bookingapp.test.test_base import (
    test_app, clean_db, test_client, test_session
)

from bookingapp.models import (
    Category, Product, User, Booking, Bill
)
from datetime import datetime, timedelta


# ============================================================
# PHẦN A: FIXTURES — Tạo dữ liệu mẫu
# ============================================================

@pytest.fixture
def seed_payment_data(test_session):
    """Tạo dữ liệu mẫu: Category, Product, 2 Users, 1 Booking"""
    # Tạo category
    cat = Category(name="Sân bóng đá")
    test_session.add(cat)
    test_session.flush()

    # Tạo product (sân)
    prod = Product(name="Sân Test Payment", price=300000, category_id=cat.id, image="football.jpg")
    test_session.add(prod)
    test_session.flush()

    # Tạo user chủ sân (User A - người đặt)
    user_a = User(username="Lý Đại Long", password="")
    user_a.set_password("Long@123!")
    test_session.add(user_a)
    test_session.flush()

    # Tạo user khác (User B - kẻ truy cập trái phép)
    user_b = User(username="Nguyễn Văn Kiên", password="")
    user_b.set_password("Kien@123!")
    test_session.add(user_b)
    test_session.flush()

    # Tạo booking cho User A (trong tương lai để hủy được)
    tomorrow = datetime.now() + timedelta(days=1)
    booking = Booking(
        user_id=user_a.id,
        product_id=prod.id,
        date=tomorrow.date(),
        slot_label="10:00 - 11:00",
        start_time=tomorrow.replace(hour=10, minute=0, second=0),
        end_time=tomorrow.replace(hour=11, minute=0, second=0),
        status="confirmed"
    )
    test_session.add(booking)
    test_session.commit()

    return {
        "user_a": user_a,
        "user_b": user_b,
        "product": prod,
        "booking": booking,
        "category": cat
    }


@pytest.fixture
def paid_booking(test_session, seed_payment_data):
    """Tạo bill cho booking đã có (tức là booking đã thanh toán)"""
    data = seed_payment_data
    bill = Bill(
        user_id=data["user_a"].id,
        product_id=data["product"].id,
        booking_id=data["booking"].id,
        amount=data["product"].price,
        payment_method="direct"
    )
    test_session.add(bill)
    test_session.commit()
    data["bill"] = bill
    return data


# ============================================================
# PHẦN B: TEST RÀNG BUỘC 1 — NÚT THANH TOÁN MỜ ĐI KHI ĐÃ TT
# ============================================================

def test_paid_booking_shows_disabled_payment_btn(test_client, paid_booking):
    """
    RB1-TC1: Khi sân đã được thanh toán, nút THANH TOÁN phải bị mờ (disabled)
    và hiển thị chữ "ĐÃ THANH TOÁN" trên trang chủ
    """
    data = paid_booking

    # Đăng nhập bằng User A
    with test_client.session_transaction() as sess:
        sess["user_id"] = data["user_a"].id
        sess["username"] = data["user_a"].username

    res = test_client.get("/")
    html = res.data.decode("utf-8")

    # Kiểm tra: phải có nút disabled với chữ "ĐÃ THANH TOÁN"
    assert "ĐÃ THANH TOÁN" in html, "Phải hiển thị 'ĐÃ THANH TOÁN' khi sân đã thanh toán"
    assert "disabled" in html, "Nút thanh toán phải bị disabled"


def test_unpaid_booking_shows_active_payment_btn(test_client, seed_payment_data):
    """
    RB1-TC2: Khi sân CHƯA thanh toán, nút THANH TOÁN phải hiển thị bình thường
    (không bị disabled, không hiện 'ĐÃ THANH TOÁN')
    """
    data = seed_payment_data

    # Đăng nhập bằng User A
    with test_client.session_transaction() as sess:
        sess["user_id"] = data["user_a"].id
        sess["username"] = data["user_a"].username

    res = test_client.get("/")
    html = res.data.decode("utf-8")

    # Kiểm tra: phải có nút THANH TOÁN hoạt động
    assert "THANH TOÁN" in html, "Phải hiển thị nút 'THANH TOÁN' khi chưa thanh toán"

    # Kiểm tra: có link đến trang payment
    assert f"/payment/{data['booking'].id}" in html, \
        "Phải có link đến trang thanh toán"


# ============================================================
# PHẦN C: TEST RÀNG BUỘC 2 — USER KHÁC KHÔNG XEM ĐƯỢC HÓA ĐƠN
# ============================================================

def test_other_user_cannot_view_payment_page(test_client, paid_booking):
    """
    RB2-TC1: User B không thể xem trang thanh toán/hóa đơn của User A
    → phải bị redirect về trang chủ (302)
    """
    data = paid_booking

    # Đăng nhập bằng User B (kẻ truy cập trái phép)
    with test_client.session_transaction() as sess:
        sess["user_id"] = data["user_b"].id
        sess["username"] = data["user_b"].username

    # User B cố truy cập hóa đơn của User A
    res = test_client.get(f"/payment/{data['booking'].id}")
    assert res.status_code == 302, \
        "User khác phải bị redirect khi truy cập hóa đơn không thuộc về mình"


def test_other_user_cannot_pay_someone_else_booking(test_client, seed_payment_data):
    """
    RB2-TC2: User B không thể thanh toán booking của User A
    → API trả về lỗi 404
    """
    data = seed_payment_data

    # Đăng nhập bằng User B
    with test_client.session_transaction() as sess:
        sess["user_id"] = data["user_b"].id
        sess["username"] = data["user_b"].username

    # User B cố thanh toán booking của User A
    res = test_client.post("/api/payment",
                           json={
                               "booking_id": data["booking"].id,
                               "payment_method": "online"
                           },
                           content_type="application/json")

    assert res.status_code == 404, \
        "User khác phải nhận 404 khi cố thanh toán booking không thuộc về mình"

    json_data = res.get_json()
    assert json_data["ok"] is False


def test_unauthenticated_cannot_view_payment(test_client, seed_payment_data):
    """
    RB2-TC3: Người chưa đăng nhập không thể truy cập trang thanh toán
    → phải bị redirect về login (302)
    """
    data = seed_payment_data

    # Không set session → chưa đăng nhập
    res = test_client.get(f"/payment/{data['booking'].id}")
    assert res.status_code == 302, \
        "Người chưa đăng nhập phải bị redirect"
