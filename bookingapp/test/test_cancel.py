import pytest
from datetime import datetime, timedelta
from bookingapp.models import User, Category, Product, Booking
from bookingapp.dao import cancel_booking_by_id, create_booking
from bookingapp.test.test_base import (test_session, test_app, test_client,
                                       confirmed_booking, sample_product,
                                       logged_in_client,logged_in_user,
                                       sample_category,sample_product,paid_booking,TimeSlot)
# ══════════════════════════════════════════════════════════
# UNIT TEST -/api/cancel-booking/
# ══════════════════════════════════════════════════════════
# HỦY THÀNH CÔNG (DÙNG PARAMETRIZE)
@pytest.mark.parametrize("username, email, product_name", [
    ("QuyenNgo", "quyen@gmail.com", "Sân Bóng Đá Quận 1"),
    ("XuyenMy", "xuyen@gmail.com", "Sân Cầu Lông Quận 7")
])
def test_cancel_multiple_success_cases(test_session, username, email, product_name):
    """Kiểm tra hủy thành công cho nhiều người dùng và sân khác nhau (Đúng chủ, > 2h)"""

    # Tạo dữ liệu mẫu từ tham số
    user = User(username=username, email=email)
    user.set_password("Test@123")
    test_session.add(user)

    cat = Category(name="Thể thao")
    test_session.add(cat)
    test_session.commit()

    product = Product(name=product_name, price=100000, category_id=cat.id)
    test_session.add(product)
    test_session.commit()

    # Tạo đơn đặt sân vào ngày mai (> 2 giờ để test hủy thành công)
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    booking, _ = create_booking(user.id, product.id, "17:00 - 18:00", tomorrow)

    # Thực hiện hủy bởi chính chủ
    result = cancel_booking_by_id(booking.id, user.id)

    #Thành công và cập nhật DB
    assert result is True
    updated_b = test_session.get(Booking, booking.id)
    assert updated_b.status == "cancelled"
    assert updated_b.user_id == user.id


# =================================================================
# 2. TEST CASE: RÀNG BUỘC 1 - CHỈ NGƯỜI ĐẶT MỚI ĐƯỢC HỦY
# =================================================================
def test_cancel_wrong_user(test_session, confirmed_booking):
    """Ràng buộc: User lạ không được hủy đơn của người khác"""

    # Tạo một User lạ (u2) không phải là chủ của confirmed_booking
    u2 = User(username="stranger", email="stranger@gmail.com")
    u2.set_password("Pass@123")
    test_session.add(u2)
    test_session.commit()

    # Dùng ID của u2 để hủy booking của người khác
    result = cancel_booking_by_id(confirmed_booking.id, u2.id)

    assert result is False
    updated_b = test_session.get(Booking, confirmed_booking.id)
    assert updated_b.status == "confirmed"


# =================================================================
# 3. TEST CASE: RÀNG BUỘC 2 - KHÔNG HỦY DƯỚI 2 GIỜ TRƯỚC GIỜ CHƠI
# =================================================================
def test_cancel_too_close_to_start(test_session, logged_in_user, sample_product):
    """Ràng buộc: Bị từ chối nếu còn dưới 2 giờ """

    #Tạo đơn hàng bắt đầu sau 1 giờ kể từ bây giờ
    near_future = datetime.now() + timedelta(hours=1)
    b = Booking(
        user_id=logged_in_user.id,
        product_id=sample_product.id,
        slot_label="Gần giờ chơi",
        date=near_future,
        start_time=near_future,
        end_time=near_future + timedelta(hours=1),
        status="confirmed"
    )
    test_session.add(b)
    test_session.commit()

    result = cancel_booking_by_id(b.id, logged_in_user.id)
    assert result is False


# =================================================================
# 4. TEST CASE: RÀNG BUỘC 3 - KHÔNG HỦY KHI ĐANG SỬ DỤNG
# =================================================================
def test_cancel_while_playing(test_session, logged_in_user, sample_product):
    """Ràng buộc: Đang trong giờ chơi (đang sử dụng sân) -> Không được hủy"""

    #Tạo đơn hàng đang diễn ra ngay lúc này
    now = datetime.now()
    b = Booking(
        user_id=logged_in_user.id,
        product_id=sample_product.id,
        slot_label="Đang đá",
        date=now,
        start_time=now - timedelta(minutes=30),
        end_time=now + timedelta(minutes=30),
        status="confirmed"
    )
    test_session.add(b)
    test_session.commit()

    result = cancel_booking_by_id(b.id, logged_in_user.id)
    assert result is False


def test_cancel_non_existent_booking(test_session, logged_in_user):
    """Test hủy một ID booking không có trong database"""
    result = cancel_booking_by_id(99999, logged_in_user.id)
    assert result is False


def test_cancel_already_cancelled_booking(test_session, logged_in_user, confirmed_booking):
    """Test không cho phép hủy một đơn đã ở trạng thái cancelled"""
    cancel_booking_by_id(confirmed_booking.id, logged_in_user.id)
    result = cancel_booking_by_id(confirmed_booking.id, logged_in_user.id)
    assert result is False


def test_cancel_booking_deletes_bill(test_session, paid_booking):
    """Ràng buộc: Khi hủy sân, hóa đơn (Bill) liên quan phải bị xóa"""
    booking, bill = paid_booking  # Mượn đồ từ test_base
    cancel_booking_by_id(booking.id, booking.user_id)

    # Kiểm tra bill có còn tồn tại không
    from bookingapp.models import Bill
    remaining_bill = test_session.get(Bill, bill.id)
    assert remaining_bill is None


def test_cancel_booking_updates_timeslot(test_app,test_session, logged_in_user, sample_product):
    """TC: Hủy đơn phải giải phóng trạng thái của TimeSlot"""
    print(test_app.url_map)
    slot = TimeSlot.query.filter_by(product_id=sample_product.id).first()

    slot.active = False
    test_session.commit()

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    booking, _ = create_booking(logged_in_user.id, sample_product.id, slot.label, tomorrow)
    cancel_booking_by_id(booking.id, logged_in_user.id)

    test_session.refresh(slot)
    assert slot.active is True


def test_cancel_past_booking(test_session, logged_in_user, sample_product):
    yesterday = datetime.now() - timedelta(days=1)
    b = Booking(
        user_id=logged_in_user.id,
        product_id=sample_product.id,
        slot_label="17:00 - 18:00",
        date=yesterday,
        start_time=yesterday.replace(hour=17, minute=0),
        end_time=yesterday.replace(hour=18, minute=0),
        status="confirmed"
    )
    test_session.add(b)
    test_session.commit()

    result = cancel_booking_by_id(b.id, logged_in_user.id)
    assert result is False


def test_cancel_allows_rebooking_within_limit(test_session, logged_in_user, sample_product):
    """
    TC: Kiểm tra sau khi hủy đơn, người dùng có thể đặt lại đơn mới
    mà không bị chặn bởi giới hạn 3 đơn/ngày.
    """
    from bookingapp.dao import create_booking, cancel_booking_by_id
    from bookingapp.models import Booking

    sel_date = (datetime.now() + timedelta(days=2)).date()

    slots = ["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00"]
    booked_ids = []
    for s in slots:
        b, _ = create_booking(logged_in_user.id, sample_product.id, s, sel_date)
        booked_ids.append(b.id)

    count_before = Booking.query.filter_by(user_id=logged_in_user.id, date=sel_date, status="confirmed").count()
    assert count_before == 3

    _, error = create_booking(logged_in_user.id, sample_product.id, "11:00 - 12:00", sel_date)
    assert error is not None

    cancel_booking_by_id(booked_ids[0], logged_in_user.id)

    new_booking, new_error = create_booking(logged_in_user.id, sample_product.id, "11:00 - 12:00", sel_date)

    assert new_error is None
    assert new_booking.status == "confirmed"

    final_count = Booking.query.filter_by(user_id=logged_in_user.id, date=sel_date, status="confirmed").count()
    assert final_count == 3


def test_cancel_booking_transaction_integrity(test_session, logged_in_user, sample_product):
    """
    Kiểm tra tính toàn vẹn: Hủy đơn có làm mất dữ liệu gốc không?
    """
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    booking, _ = create_booking(logged_in_user.id, sample_product.id, "08:00 - 09:00", tomorrow)

    cancel_booking_by_id(booking.id, logged_in_user.id)

    b_in_db = test_session.get(Booking, booking.id)
    assert b_in_db is not None
    assert b_in_db.status == "cancelled"

    assert test_session.get(Product, sample_product.id) is not None
    assert test_session.get(User, logged_in_user.id) is not None

# ══════════════════════════════════════════════════════════
# API TEST -/api/cancel-booking/
# ══════════════════════════════════════════════════════════
def test_api_cancel_booking_unauthorized(test_client, confirmed_booking):
    """
    API Test: Người dùng chưa đăng nhập gọi API hủy thì phải bị chặn
    """
    response = test_client.post(f"/api/cancel-booking/{confirmed_booking.id}")
    assert response.status_code == 302

def test_api_cancel_invalid_id(logged_in_client):
    """
    API Test: Gửi ID đơn hàng không tồn tại
    """
    response = logged_in_client.post("/api/cancel-booking/abc")
    assert response.status_code == 404


def test_api_cancel_multiple_times(logged_in_client, confirmed_booking):
    """
    API Test: Nhận 2 lệnh hủy cho cùng 1 đơn hàng
    """

    res1 = logged_in_client.post(f"/api/cancel-booking/{confirmed_booking.id}")
    assert res1.status_code == 302
    res2 = logged_in_client.post(f"/api/cancel-booking/{confirmed_booking.id}")
    assert res2.status_code == 302

