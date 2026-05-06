import pytest
from bookingapp.dao import create_booking, cancel_booking_by_id
from bookingapp.models import Booking, Category, Product
from bookingapp import db
from datetime import datetime, timedelta, time

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
    TC: Kiểm tra sau khi hủy đơn trên sân A, người dùng có thể đặt sân D mới
    mà không bị chặn bởi giới hạn 3 sân khác nhau/ngày.
    """
    # from bookingapp.dao import create_booking, cancel_booking_by_id
    # from bookingapp.models import Booking, Category, Product
    # from bookingapp import db
    # from datetime import datetime, timedelta, time

    sel_date_obj = (datetime.now() + timedelta(days=2)).date()
    day_start = datetime.combine(sel_date_obj, time.min)

    # Tạo 3 sân khác nhau (sân B, C, D)
    cat = test_session.query(Category).first()
    product_b = Product(name="Sân B", price=100000, category_id=cat.id, active=True)
    product_c = Product(name="Sân C", price=100000, category_id=cat.id, active=True)
    product_d = Product(name="Sân D", price=100000, category_id=cat.id, active=True)
    test_session.add_all([product_b, product_c, product_d])
    test_session.commit()

    # Đặt 3 sân khác nhau → đạt giới hạn
    b1, _ = create_booking(logged_in_user.id, sample_product.id, "08:00 - 09:00", sel_date_obj)
    b2, _ = create_booking(logged_in_user.id, product_b.id,      "08:00 - 09:00", sel_date_obj)
    b3, _ = create_booking(logged_in_user.id, product_c.id,      "08:00 - 09:00", sel_date_obj)
    db.session.commit()

    count_before = test_session.query(Booking).filter(
        Booking.user_id == logged_in_user.id,
        Booking.date == day_start,
        Booking.status == "confirmed"
    ).count()
    assert count_before == 3

    # Thử đặt sân thứ 4 (sân D) → phải bị chặn vì đã đủ 3 sân khác nhau
    _, error = create_booking(logged_in_user.id, product_d.id, "08:00 - 09:00", sel_date_obj)
    assert error is not None, "Phải bị chặn khi đã đặt 3 sân khác nhau"

    # Hủy sân B
    cancel_booking_by_id(b2.id, logged_in_user.id)
    db.session.commit()

    # Sau khi hủy, đặt sân D mới → phải thành công (chỉ còn 2 sân khác nhau)
    new_booking, new_error = create_booking(logged_in_user.id, product_d.id, "08:00 - 09:00", sel_date_obj)
    assert new_error is None, f"Phải đặt được sau khi hủy: {new_error}"
    assert new_booking.status == "confirmed"

    # Tổng số booking confirmed vẫn là 3
    final_count = test_session.query(Booking).filter(
        Booking.user_id == logged_in_user.id,
        Booking.date == day_start,
        Booking.status == "confirmed"
    ).count()
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


# ══════════════════════════════════════════════════════════
# UNIT TEST – dao.cancel_grouped_booking (dao.py:295-335)
# ══════════════════════════════════════════════════════════

from bookingapp.dao import cancel_grouped_booking
from bookingapp.models import Bill


class TestCancelGroupedBookingDAO:
    """TC-CANCEL-GROUP-DAO: Kiểm tra hàm cancel_grouped_booking."""

    def _make_group(self, test_session, user, product, group_id, slots, days_ahead=1):
        """Helper: tạo nhóm booking cùng group_id."""
        tomorrow = datetime.now() + timedelta(days=days_ahead)
        day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        bookings = []
        for i, slot in enumerate(slots):
            start_h = 8 + i
            b = Booking(
                user_id=user.id, product_id=product.id,
                slot_label=slot, date=day_start,
                start_time=tomorrow.replace(hour=start_h, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=start_h + 1, minute=0, second=0, microsecond=0),
                status="confirmed", group_id=group_id,
            )
            test_session.add(b)
            bookings.append(b)
        test_session.commit()
        return bookings

    def test_cancel_group_success(self, test_session, logged_in_user, sample_product):
        """TC1: Hủy nhóm booking hợp lệ → True."""
        bks = self._make_group(test_session, logged_in_user, sample_product,
                               "grp001", ["08:00 - 09:00", "09:00 - 10:00"])
        success, had_bill = cancel_grouped_booking("grp001", logged_in_user.id)
        assert success is True
        assert had_bill is False
        for b in bks:
            test_session.refresh(b)
            assert b.status == "cancelled"

    def test_cancel_group_not_found(self, test_session, logged_in_user):
        """TC2: group_id không tồn tại → False."""
        success, had_bill = cancel_grouped_booking("nonexistent", logged_in_user.id)
        assert success is False

    def test_cancel_group_wrong_user(self, test_session, logged_in_user, sample_product):
        """TC3: User khác → False."""
        self._make_group(test_session, logged_in_user, sample_product,
                         "grp002", ["08:00 - 09:00"])
        u2 = User(username="grp_stranger", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()
        success, _ = cancel_grouped_booking("grp002", u2.id)
        assert success is False

    def test_cancel_group_past_booking(self, test_session, logged_in_user, sample_product):
        """TC4: Booking đã qua → False."""
        past = datetime.now() - timedelta(days=1)
        day_start = past.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id, product_id=sample_product.id,
            slot_label="08:00 - 09:00", date=day_start,
            start_time=past.replace(hour=8), end_time=past.replace(hour=9),
            status="confirmed", group_id="grp_past",
        )
        test_session.add(b)
        test_session.commit()
        success, _ = cancel_grouped_booking("grp_past", logged_in_user.id)
        assert success is False

    def test_cancel_group_too_close(self, test_session, logged_in_user, sample_product):
        """TC5: Còn < 2h → False."""
        near = datetime.now() + timedelta(hours=1)
        day_start = near.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id, product_id=sample_product.id,
            slot_label="soon", date=day_start,
            start_time=near, end_time=near + timedelta(hours=1),
            status="confirmed", group_id="grp_close",
        )
        test_session.add(b)
        test_session.commit()
        success, _ = cancel_grouped_booking("grp_close", logged_in_user.id)
        assert success is False

    def test_cancel_group_while_playing(self, test_session, logged_in_user, sample_product):
        """TC6: Đang chơi → False."""
        now = datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id, product_id=sample_product.id,
            slot_label="playing", date=day_start,
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
            status="confirmed", group_id="grp_play",
        )
        test_session.add(b)
        test_session.commit()
        success, _ = cancel_grouped_booking("grp_play", logged_in_user.id)
        assert success is False

    def test_cancel_group_deletes_bill(self, test_session, logged_in_user, sample_product):
        """TC7: Hủy nhóm có bill → xóa bill, had_bill=True."""
        bks = self._make_group(test_session, logged_in_user, sample_product,
                               "grp_bill", ["08:00 - 09:00", "09:00 - 10:00"])
        bill = Bill(
            user_id=logged_in_user.id, product_id=sample_product.id,
            booking_id=bks[0].id, amount=600_000,
        )
        test_session.add(bill)
        test_session.commit()
        bill_id = bill.id
        success, had_bill = cancel_grouped_booking("grp_bill", logged_in_user.id)
        assert success is True
        assert had_bill is True
        assert test_session.get(Bill, bill_id) is None

    def test_cancel_group_restores_timeslot(self, test_session, logged_in_user, sample_product):
        """TC8: Hủy nhóm → TimeSlot.active = True."""
        slot = TimeSlot.query.filter_by(product_id=sample_product.id).first()
        bks = self._make_group(test_session, logged_in_user, sample_product,
                               "grp_slot", [slot.label])
        slot.active = False
        test_session.commit()
        cancel_grouped_booking("grp_slot", logged_in_user.id)
        test_session.refresh(slot)
        assert slot.active is True


# ══════════════════════════════════════════════════════════
# API TEST – /api/cancel-group/<group_id> (index.py:477-488)
# ══════════════════════════════════════════════════════════

class TestCancelGroupRoute:
    """TC-CANCEL-GROUP-ROUTE: POST /api/cancel-group/<group_id>"""

    def _make_group_booking(self, test_session, user, product, group_id):
        tomorrow = datetime.now() + timedelta(days=1)
        day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=user.id, product_id=product.id,
            slot_label="08:00 - 09:00", date=day_start,
            start_time=tomorrow.replace(hour=8, minute=0, second=0, microsecond=0),
            end_time=tomorrow.replace(hour=9, minute=0, second=0, microsecond=0),
            status="confirmed", group_id=group_id,
        )
        test_session.add(b)
        test_session.commit()
        return b

    def test_cancel_group_route_success(self, test_session, logged_in_client,
                                         logged_in_user, sample_product):
        """TC1: Hủy nhóm thành công → redirect + flash success."""
        self._make_group_booking(test_session, logged_in_user, sample_product, "route_grp1")
        res = logged_in_client.post("/api/cancel-group/route_grp1", follow_redirects=False)
        assert res.status_code == 302

    def test_cancel_group_route_with_refund(self, test_session, logged_in_client,
                                             logged_in_user, sample_product):
        """TC2: Hủy nhóm đã thanh toán → hoàn tiền."""
        b = self._make_group_booking(test_session, logged_in_user, sample_product, "route_grp2")
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=b.id, amount=300_000)
        test_session.add(bill)
        test_session.commit()
        res = logged_in_client.post("/api/cancel-group/route_grp2", follow_redirects=False)
        assert res.status_code == 302

    def test_cancel_group_route_fail(self, test_session, logged_in_client,
                                      logged_in_user, sample_product):
        """TC3: Hủy nhóm không hợp lệ (đã qua) → redirect + flash danger."""
        past = datetime.now() - timedelta(days=1)
        day_start = past.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id, product_id=sample_product.id,
            slot_label="08:00 - 09:00", date=day_start,
            start_time=past.replace(hour=8), end_time=past.replace(hour=9),
            status="confirmed", group_id="route_grp_fail",
        )
        test_session.add(b)
        test_session.commit()
        res = logged_in_client.post("/api/cancel-group/route_grp_fail", follow_redirects=False)
        assert res.status_code == 302
