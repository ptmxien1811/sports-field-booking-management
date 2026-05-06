"""
test_booking.py – Kiểm thử đặt sân (CR100-BOOKING)
Bao gồm: Unit test dao.create_booking(), API test /api/book, cancel route
"""

import pytest
from bookingapp.models import User, Product, Category, Booking, Bill
from bookingapp import db
from bookingapp.dao import create_booking, cancel_booking_by_id
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ''))

from bookingapp.test.test_base import  (
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking, paid_booking,
    admin_user, admin_client,
)


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – dao.create_booking()
# ═══════════════════════════════════════════════════════════════════

class TestCreateBookingDAO:
    """TC-BOOK-DAO: Kiểm tra logic nghiệp vụ create_booking."""

    def test_booking_success(self, test_session, logged_in_user, sample_product):
        """ Đặt sân hợp lệ → thành công."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        booking, err = create_booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="08:00 - 09:00",
            date_obj=tomorrow,
        )
        assert err is None
        assert booking is not None
        assert booking.status == "confirmed"
        assert booking.user_id == logged_in_user.id
        assert booking.product_id == sample_product.id

    def test_booking_past_date_rejected(self, test_session, logged_in_user, sample_product):
        """ Không đặt sân trong quá khứ."""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        booking, err = create_booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="08:00 - 09:00",
            date_obj=yesterday,
        )
        assert booking is None
        assert err is not None
        assert "quá khứ" in err

    def test_booking_slot_less_than_1_hour_rejected(self, test_session, logged_in_user,
                                                     sample_product):
        """ Khung giờ < 1 tiếng bị từ chối."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        booking, err = create_booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="08:00 - 08:30",
            date_obj=tomorrow,
        )
        assert booking is None
        assert err is not None
        assert "1 giờ" in err

    def test_booking_max_3_per_day(self, test_session, logged_in_user):
        """ Không đặt quá 3 sân/ngày."""
        c = Category(name="Cat3/day")
        test_session.add(c)
        test_session.commit()

        tomorrow = (datetime.now() + timedelta(days=1)).date()
        slots = ["08:00 - 09:00", "10:00 - 11:00", "13:00 - 14:00", "15:00 - 16:00"]

        products = []
        for i in range(4):
            p = Product(name=f"San3perday_{i}", price=100_000, category_id=c.id)
            test_session.add(p)
            test_session.commit()
            products.append(p)

        # Đặt 3 sân đầu thành công
        for i in range(3):
            b, err = create_booking(logged_in_user.id, products[i].id, slots[i], tomorrow)
            assert err is None, f"Lần {i+1} phải thành công"

        # Lần thứ 4 phải thất bại
        b4, err4 = create_booking(logged_in_user.id, products[3].id, slots[3], tomorrow)
        assert b4 is None
        assert err4 is not None
        assert "tối đa 3" in err4

    def test_booking_conflict_same_slot_same_product(self, test_session, logged_in_user,
                                                      sample_product):
        """ Trùng slot cùng sân → từ chối."""
        u2 = User(username="u2_conflict", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()

        tomorrow = (datetime.now() + timedelta(days=1)).date()
        b1, err1 = create_booking(logged_in_user.id, sample_product.id, "08:00 - 09:00", tomorrow)
        assert err1 is None

        b2, err2 = create_booking(u2.id, sample_product.id, "08:00 - 09:00", tomorrow)
        assert b2 is None
        assert "đã được đặt" in err2

    def test_booking_different_slots_same_product_allowed(self, test_session, logged_in_user,
                                                           sample_product):
        """ Khác slot cùng sân → được phép."""
        u2 = User(username="u2_diffslot", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()

        tomorrow = (datetime.now() + timedelta(days=1)).date()
        b1, err1 = create_booking(logged_in_user.id, sample_product.id, "08:00 - 09:00", tomorrow)
        b2, err2 = create_booking(u2.id, sample_product.id, "10:00 - 11:00", tomorrow)

        assert err1 is None
        assert err2 is None

    def test_booking_same_slot_different_products_allowed(self, test_session, logged_in_user,
                                                           sample_category):
        """ Cùng slot nhưng khác sân → được phép (user đặt 2 sân khác nhau)."""
        p1 = Product(name="San_diff1", price=100_000, category_id=sample_category.id)
        p2 = Product(name="San_diff2", price=100_000, category_id=sample_category.id)
        test_session.add_all([p1, p2])
        test_session.commit()

        tomorrow = (datetime.now() + timedelta(days=1)).date()
        b1, err1 = create_booking(logged_in_user.id, p1.id, "08:00 - 09:00", tomorrow)
        b2, err2 = create_booking(logged_in_user.id, p2.id, "08:00 - 09:00", tomorrow)

        assert err1 is None
        assert err2 is None

    def test_booking_saves_correct_times(self, test_session, logged_in_user, sample_product):
        """ start_time và end_time lưu đúng."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        booking, _ = create_booking(logged_in_user.id, sample_product.id,
                                    "09:00 - 10:00", tomorrow)
        assert booking.start_time.hour == 9
        assert booking.end_time.hour == 10

    def test_booking_different_days_independent(self, test_session, logged_in_user,
                                                 sample_category):
        """ Giới hạn 3/ngày chỉ áp dụng trong ngày, ngày khác reset."""
        c = Category(name="CatDays")
        test_session.add(c)
        test_session.commit()

        products = []
        for i in range(4):
            p = Product(name=f"SanDay_{i}", price=100_000, category_id=c.id)
            test_session.add(p)
            test_session.commit()
            products.append(p)

        day1 = (datetime.now() + timedelta(days=1)).date()
        day2 = (datetime.now() + timedelta(days=2)).date()
        slot = "08:00 - 09:00"

        # Đặt 3 sân ngày 1
        for i in range(3):
            b, err = create_booking(logged_in_user.id, products[i].id, slot, day1)
            assert err is None

        # Ngày 2 vẫn cho phép đặt
        b4, err4 = create_booking(logged_in_user.id, products[3].id, slot, day2)
        assert err4 is None


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: UNIT TEST – dao.cancel_booking_by_id()
# ═══════════════════════════════════════════════════════════════════

class TestCancelBookingDAO:
    """TC-CANCEL-DAO: Kiểm tra hàm cancel_booking_by_id."""

    def test_cancel_success(self, test_session, logged_in_user, confirmed_booking):
        """: Hủy sân của chính mình thành công → status='cancelled'."""
        result = cancel_booking_by_id(confirmed_booking.id, logged_in_user.id)
        assert result is True
        updated = Booking.query.get(confirmed_booking.id)
        assert updated.status == "cancelled"

    def test_cancel_wrong_user(self, test_session, confirmed_booking):
        """ User khác không được hủy sân."""
        u2 = User(username="other_cancel", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()

        result = cancel_booking_by_id(confirmed_booking.id, u2.id)
        assert result is False

    def test_cancel_nonexistent_booking(self, test_session, logged_in_user):
        """ Booking không tồn tại → False."""
        result = cancel_booking_by_id(99999, logged_in_user.id)
        assert result is False

    def test_cancel_time_constraint_ok(self, test_session, logged_in_user, sample_product):
        """ Còn hơn 2 giờ → điều kiện được phép hủy."""
        future = datetime.now() + timedelta(hours=3)
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="20:00 - 21:00",
            date=future.replace(hour=0, minute=0, second=0, microsecond=0),
            start_time=future,
            end_time=future + timedelta(hours=1),
            status="confirmed",
        )
        test_session.add(b)
        test_session.commit()

        time_until_hours = (b.start_time - datetime.now()).total_seconds() / 3600
        assert time_until_hours > 2  # điều kiện cho phép hủy

    def test_cancel_time_constraint_denied(self, test_session, logged_in_user, sample_product):
        """ Còn < 2 giờ → điều kiện KHÔNG cho phép hủy."""
        future = datetime.now() + timedelta(hours=1, minutes=30)
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="19:00 - 20:00",
            date=future.replace(hour=0, minute=0, second=0, microsecond=0),
            start_time=future,
            end_time=future + timedelta(hours=1),
            status="confirmed",
        )
        test_session.add(b)
        test_session.commit()

        time_until_hours = (b.start_time - datetime.now()).total_seconds() / 3600
        assert time_until_hours < 2  # điều kiện không cho phép hủy

    def test_cancel_while_playing(self, test_session, logged_in_user, sample_product):
        """ Đang trong giờ chơi → không được hủy."""
        now = datetime.now()
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="now",
            date=now.replace(hour=0, minute=0, second=0, microsecond=0),
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
            status="confirmed",
        )
        test_session.add(b)
        test_session.commit()

        is_playing = b.start_time <= now <= b.end_time
        assert is_playing is True  # Phải đang trong giờ → không được hủy

    def test_cancel_after_end_time(self, test_session, logged_in_user, sample_product):
        """ Đã qua giờ chơi → không được hủy."""
        past = datetime.now() - timedelta(hours=2)
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="07:00 - 08:00",
            date=past.replace(hour=0, minute=0, second=0, microsecond=0),
            start_time=past - timedelta(hours=1),
            end_time=past,
            status="confirmed",
        )
        test_session.add(b)
        test_session.commit()

        already_ended = datetime.now() > b.end_time
        assert already_ended is True  # Đã sử dụng → không hủy được


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: API TEST – POST /api/book
# ═══════════════════════════════════════════════════════════════════

class TestBookAPI:
    """TC-BOOK-API: POST /api/book"""

    def test_book_unauthenticated(self, test_client, sample_product):
        """ Chưa đăng nhập → 401."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = test_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": tomorrow,
        })
        assert res.status_code == 401
        data = res.get_json()
        assert data["ok"] is False

    def test_book_success(self, logged_in_client, sample_product):
        """ Đăng nhập, slot hợp lệ → đặt thành công."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": tomorrow,
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert "booking_ids" in data

    def test_book_multiple_slots(self, logged_in_client, sample_product):
        """ Đặt nhiều slot cùng lúc (list slots)."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slots": ["08:00 - 09:00", "10:00 - 11:00"],
            "date": tomorrow,
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert len(data["booking_ids"]) == 2

    def test_book_no_slot_provided(self, logged_in_client, sample_product):
        """ Không chọn slot → lỗi 400."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slots": [],
            "date": tomorrow,
        })
        assert res.status_code == 400
        data = res.get_json()
        assert data["ok"] is False

    def test_book_invalid_date(self, logged_in_client, sample_product):
        """ Ngày không hợp lệ → 400."""
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": "not-a-date",
        })
        assert res.status_code == 400

    def test_book_duplicate_slot_returns_error(self, logged_in_client, sample_product):
        """ Slot đã được người khác đặt → lỗi."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        # Đặt lần đầu
        logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": tomorrow,
        })
        # Đặt lần 2 cùng slot
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": tomorrow,
        })
        data = res.get_json()
        # ok = False hoặc có error trong message
        assert data["ok"] is False or "thất bại" in data.get("msg", "")


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: API TEST – POST /api/cancel-booking/<id>
# ═══════════════════════════════════════════════════════════════════

class TestCancelBookingRoute:
    """TC-CANCEL-ROUTE: POST /api/cancel-booking/<id>"""

    def test_cancel_route_success(self, logged_in_client, confirmed_booking):
        """ Hủy sân hợp lệ → redirect với flash success."""
        res = logged_in_client.post(
            f"/api/cancel-booking/{confirmed_booking.id}",
            follow_redirects=False,
        )
        assert res.status_code == 302

    def test_cancel_route_with_refund(self, test_session, logged_in_client,
                                       paid_booking):
        """ Hủy sân đã thanh toán → hoàn tiền (xóa bill)."""
        booking, bill = paid_booking
        bill_id = bill.id

        res = logged_in_client.post(
            f"/api/cancel-booking/{booking.id}",
            follow_redirects=False,
        )
        assert res.status_code == 302
        remaining_bill = Bill.query.get(bill_id)
        assert remaining_bill is None  # Bill đã bị xóa (hoàn tiền)

    def test_cancel_route_wrong_user(self, test_session, test_client, confirmed_booking):
        """ User khác không được hủy sân → redirect."""
        u2 = User(username="other_route", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()

        with test_client.session_transaction() as sess:
            sess["user_id"] = u2.id
            sess["username"] = u2.username

        res = test_client.post(
            f"/api/cancel-booking/{confirmed_booking.id}",
            follow_redirects=False,
        )
        assert res.status_code == 302  # redirect về home

    def test_cancel_route_unauthenticated(self, test_client, confirmed_booking):
        """ Chưa đăng nhập → redirect."""
        res = test_client.post(
            f"/api/cancel-booking/{confirmed_booking.id}",
            follow_redirects=False,
        )
        # Booking không tìm thấy (user_id không khớp) → redirect
        assert res.status_code == 302

    def test_cancel_route_nonexistent(self, logged_in_client):
        """ Booking không tồn tại → redirect."""
        res = logged_in_client.post(
            "/api/cancel-booking/99999",
            follow_redirects=False,
        )
        assert res.status_code == 302


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: API TEST – /api/my-bookings + /api/my-bookings-detail
# ═══════════════════════════════════════════════════════════════════

class TestMyBookingsAPI:
    """TC-BOOK-MY: GET /api/my-bookings & /api/my-bookings-detail"""

    def test_my_bookings_count(self, logged_in_client, confirmed_booking):
        """ Số lượng booking trả về đúng."""
        res = logged_in_client.get("/api/my-bookings")
        data = res.get_json()
        assert data["bookings"] == 1

    def test_my_bookings_unauthenticated(self, test_client):
        """Chưa đăng nhập → 401."""
        res = test_client.get("/api/my-bookings")
        assert res.status_code == 401

    def test_my_bookings_detail_structure(self, logged_in_client, confirmed_booking):
        """ Detail trả về đúng các field."""
        res = logged_in_client.get("/api/my-bookings-detail")
        data = res.get_json()
        assert "items" in data
        assert len(data["items"]) >= 1
        item = data["items"][0]
        for field in ["id", "product_name", "slot_label", "date_str", "status"]:
            assert field in item

    def test_my_bookings_empty(self, logged_in_client):
        """ User chưa có booking → items rỗng."""
        res = logged_in_client.get("/api/my-bookings-detail")
        data = res.get_json()
        assert data["items"] == []


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: UNIT TEST – dao.get_bookings_by_user (dao.py:16)
# ═══════════════════════════════════════════════════════════════════

class TestGetBookingsByUserDAO:
    """TC-BOOK-GETDAO: Kiểm tra dao.get_bookings_by_user."""

    def test_get_bookings_returns_confirmed(self, test_session, logged_in_user, confirmed_booking):
        from bookingapp.dao import get_bookings_by_user
        bookings = get_bookings_by_user(logged_in_user.id)
        assert len(bookings) == 1
        assert bookings[0].status == "confirmed"

    def test_get_bookings_excludes_cancelled(self, test_session, logged_in_user, confirmed_booking):
        from bookingapp.dao import get_bookings_by_user
        confirmed_booking.status = "cancelled"
        test_session.commit()
        bookings = get_bookings_by_user(logged_in_user.id)
        assert len(bookings) == 0

    def test_get_bookings_empty_for_new_user(self, test_session, logged_in_user):
        from bookingapp.dao import get_bookings_by_user
        bookings = get_bookings_by_user(logged_in_user.id)
        assert bookings == []


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: API TEST – group_id edge cases (index.py:380-382, 392)
# ═══════════════════════════════════════════════════════════════════

class TestBookGroupEdgeCases:
    """TC-BOOK-GROUP: Kiểm tra group_id và partial failure."""

    def test_book_multi_slots_one_fails_clears_group_id(self, logged_in_client, sample_product):
        """ Đặt 2 slot nhưng 1 slot trong quá khứ → chỉ 1 thành công, group_id=None."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        yesterday = str((datetime.now() - timedelta(days=1)).date())
        # Đặt lần đầu slot hợp lệ rồi đặt lại cùng slot → trùng
        logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": tomorrow,
        })
        # Đặt 2 slot: 1 trùng (08:00) + 1 mới (10:00)
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slots": ["08:00 - 09:00", "10:00 - 11:00"],
            "date": tomorrow,
        })
        data = res.get_json()
        assert data["ok"] is True
        assert len(data["booking_ids"]) == 1
        # Booking thành công phải không có group_id (vì chỉ 1 cái thành công)
        b = Booking.query.get(data["booking_ids"][0])
        assert b.group_id is None

    def test_book_multi_slots_partial_failure_message(self, logged_in_client, sample_product):
        """ Đặt 2 slot, 1 thất bại → msg chứa 'thất bại' (index.py:392)."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        # Đặt 1 slot trước
        logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slot": "08:00 - 09:00",
            "date": tomorrow,
        })
        # Đặt 2 slot: 1 trùng + 1 mới
        res = logged_in_client.post("/api/book", json={
            "product_id": sample_product.id,
            "slots": ["08:00 - 09:00", "10:00 - 11:00"],
            "date": tomorrow,
        })
        data = res.get_json()
        assert data["ok"] is True
        assert "thất bại" in data["msg"]