"""
test_venue.py – Kiểm thử trang chi tiết sân (CR-VENUE)
Bao gồm: DB test Product/TimeSlot, API test /venue/<id>, /api/slots
"""

import pytest
from bookingapp.models import Product, Category, TimeSlot, Booking, Review, User
from bookingapp import db
from bookingapp.dao import get_product_by_id, get_slots_for_product_date
from datetime import datetime, timedelta, date as date_type

from bookingapp.test.test_base import (
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking,)


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – DB / Model Product
# ═══════════════════════════════════════════════════════════════════

class TestProductModel:
    """TC-VENUE-MODEL: Kiểm tra model Product trong DB."""

    def test_create_product(self, test_session, sample_category):
        """TC1: Tạo sân thành công."""
        p = Product(name="Sân Test 1", price=200_000, category_id=sample_category.id)
        test_session.add(p)
        test_session.commit()
        found = Product.query.filter_by(name="Sân Test 1").first()
        assert found is not None
        assert found.price == 200_000

    def test_product_name_unique(self, test_session, sample_category):
        """TC2: Tên sân phải duy nhất (unique constraint)."""
        from sqlalchemy.exc import IntegrityError
        p1 = Product(name="Sân Trùng", price=100_000, category_id=sample_category.id)
        p2 = Product(name="Sân Trùng", price=200_000, category_id=sample_category.id)
        test_session.add(p1)
        test_session.commit()
        test_session.add(p2)
        with pytest.raises(Exception):
            test_session.commit()

    def test_product_active_default_true(self, test_session, sample_category):
        """TC3: active mặc định là True."""
        p = Product(name="Sân Active Test", price=100_000, category_id=sample_category.id)
        test_session.add(p)
        test_session.commit()
        assert p.active is True

    def test_product_avg_rating_no_reviews(self, test_session, sample_product):
        """TC4: avg_rating = 0 khi chưa có review."""
        assert sample_product.avg_rating == 0

    def test_product_avg_rating_with_reviews(self, test_session, sample_product, logged_in_user):
        """TC5: avg_rating tính đúng trung bình."""
        r1 = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                    rating=4, content="Tốt")
        test_session.add(r1)

        u2 = User(username="u2", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()

        r2 = Review(product_id=sample_product.id, user_id=u2.id, rating=2, content="Bình thường")
        test_session.add(r2)
        test_session.commit()

        test_session.refresh(sample_product)
        assert sample_product.avg_rating == 3.0

    def test_product_category_relationship(self, test_session, sample_product, sample_category):
        """TC6: Quan hệ Product → Category đúng."""
        assert sample_product.category.name == sample_category.name

    def test_product_cascade_delete_bookings(self, test_session, sample_product, confirmed_booking):
        """TC7: Xóa Product xóa cascade Booking liên quan."""
        product_id = sample_product.id
        test_session.delete(sample_product)
        test_session.commit()
        remaining = Booking.query.filter_by(product_id=product_id).all()
        assert len(remaining) == 0


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: UNIT TEST – TimeSlot
# ═══════════════════════════════════════════════════════════════════

class TestTimeSlot:
    """TC-VENUE-SLOT: Kiểm tra TimeSlot model."""

    def test_timeslot_created_with_product(self, test_session, sample_product):
        """TC1: TimeSlot liên kết đúng với Product."""
        slots = TimeSlot.query.filter_by(product_id=sample_product.id).all()
        assert len(slots) == 3  # 3 slots trong fixture

    def test_timeslot_label(self, test_session, sample_product):
        """TC2: Label của slot đúng."""
        slot = TimeSlot.query.filter_by(product_id=sample_product.id,
                                        label="08:00 - 09:00").first()
        assert slot is not None
        assert slot.period == "morning"

    def test_timeslot_str(self, test_session, sample_product):
        """TC3: __str__ trả về label."""
        slot = TimeSlot.query.filter_by(product_id=sample_product.id).first()
        assert str(slot) == slot.label


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: UNIT TEST – dao.get_slots_for_product_date()
# ═══════════════════════════════════════════════════════════════════

class TestGetSlotsDAO:
    """TC-VENUE-DAO: Kiểm tra hàm get_slots_for_product_date."""

    def test_all_slots_available_no_bookings(self, test_session, sample_product):
        """TC1: Tất cả slot trống khi chưa có booking."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        slots_data, available = get_slots_for_product_date(sample_product.id, tomorrow)
        assert available == 3  # 3 slots trong fixture
        for period_slots in slots_data.values():
            for s in period_slots:
                assert s["booked"] is False

    def test_slot_marked_booked_after_booking(self, test_session, sample_product,
                                               logged_in_user, confirmed_booking):
        """TC2: Slot đã đặt → booked=True."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        slots_data, available = get_slots_for_product_date(sample_product.id, tomorrow)
        all_slots = [s for p in slots_data.values() for s in p]
        booked_slots = [s for s in all_slots if s["booked"]]
        assert len(booked_slots) == 1
        assert booked_slots[0]["label"] == "09:00 - 10:00"

    def test_available_count_decreases_after_booking(self, test_session, sample_product,
                                                      logged_in_user, confirmed_booking):
        """TC3: Số slot available giảm sau khi đặt."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        _, available = get_slots_for_product_date(sample_product.id, tomorrow)
        assert available == 2  # 3 - 1

    def test_different_date_has_full_availability(self, test_session, sample_product,
                                                   confirmed_booking):
        """TC4: Ngày khác không ảnh hưởng slot ngày hôm nay."""
        day_after = (datetime.now() + timedelta(days=2)).date()
        _, available = get_slots_for_product_date(sample_product.id, day_after)
        assert available == 3


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: API TEST – GET /venue/<id>
# ═══════════════════════════════════════════════════════════════════

class TestVenueDetailRoute:
    """TC-VENUE-ROUTE: GET /venue/<id>"""

    def test_venue_detail_success(self, test_client, sample_product):
        """TC1: Truy cập trang chi tiết sân thành công (200)."""
        res = test_client.get(f"/venue/{sample_product.id}")
        assert res.status_code == 200

    def test_venue_detail_not_found(self, test_client):
        """TC2: Sân không tồn tại → 404."""
        res = test_client.get("/venue/99999")
        assert res.status_code == 404

    def test_venue_detail_shows_product_name(self, test_client, sample_product):
        """TC3: Trang hiển thị tên sân."""
        res = test_client.get(f"/venue/{sample_product.id}")
        assert sample_product.name.encode() in res.data

    def test_venue_detail_can_review_false_when_not_booked(self, logged_in_client, sample_product):
        """TC4: User chưa đặt → can_review = False."""
        res = logged_in_client.get(f"/venue/{sample_product.id}")
        assert res.status_code == 200
        # Page renders mà không hiện form review
        # (kiểm tra gián tiếp qua API can-review)

    def test_venue_detail_unauthenticated(self, test_client, sample_product):
        """TC5: Guest (chưa đăng nhập) vẫn xem được trang chi tiết."""
        res = test_client.get(f"/venue/{sample_product.id}")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: API TEST – GET /api/slots/<product_id>
# ═══════════════════════════════════════════════════════════════════

class TestSlotsAPI:
    """TC-VENUE-SLOTS-API: GET /api/slots/<id>?date=..."""

    def test_api_slots_returns_json(self, test_client, sample_product):
        """TC1: API trả về JSON hợp lệ."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = test_client.get(f"/api/slots/{sample_product.id}?date={tomorrow}")
        assert res.status_code == 200
        data = res.get_json()
        assert "slots" in data
        assert "available" in data

    def test_api_slots_available_count(self, test_client, sample_product):
        """TC2: Số slot available đúng."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = test_client.get(f"/api/slots/{sample_product.id}?date={tomorrow}")
        data = res.get_json()
        assert data["available"] == 3

    def test_api_slots_max_per_day_returned(self, test_client, sample_product):
        """TC3: max_per_day trả về 3."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = test_client.get(f"/api/slots/{sample_product.id}?date={tomorrow}")
        data = res.get_json()
        assert data["max_per_day"] == 3

    def test_api_slots_invalid_date_falls_back_today(self, test_client, sample_product):
        """TC4: Date không hợp lệ → fallback về hôm nay, không crash."""
        res = test_client.get(f"/api/slots/{sample_product.id}?date=invalid")
        assert res.status_code == 200

    def test_api_slots_bookings_today_count_for_logged_in(self, logged_in_client,
                                                            sample_product, confirmed_booking):
        """TC5: Trả về bookings_today đúng cho user đăng nhập."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = logged_in_client.get(f"/api/slots/{sample_product.id}?date={tomorrow}")
        data = res.get_json()
        assert data["bookings_today"] == 1

    def test_api_slots_bookings_today_zero_for_guest(self, test_client, sample_product):
        """TC6: Guest → bookings_today = 0."""
        tomorrow = str((datetime.now() + timedelta(days=1)).date())
        res = test_client.get(f"/api/slots/{sample_product.id}?date={tomorrow}")
        data = res.get_json()
        assert data["bookings_today"] == 0


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: API TEST – /api/can-review/<product_id>
# ═══════════════════════════════════════════════════════════════════

class TestCanReviewAPI:
    """TC-VENUE-CANREVIEW: GET /api/can-review/<id>"""

    def test_can_review_not_logged_in(self, test_client, sample_product):
        """TC1: Chưa đăng nhập → can_review=False, reason=not_logged_in."""
        res = test_client.get(f"/api/can-review/{sample_product.id}")
        data = res.get_json()
        assert data["can_review"] is False
        assert data["reason"] == "not_logged_in"

    def test_can_review_not_booked(self, logged_in_client, sample_product):
        """TC2: Chưa đặt sân → can_review=False, reason=not_booked."""
        res = logged_in_client.get(f"/api/can-review/{sample_product.id}")
        data = res.get_json()
        assert data["can_review"] is False
        assert data["reason"] == "not_booked"

    def test_can_review_booked_not_reviewed(self, logged_in_client, sample_product,
                                             confirmed_booking):
        """TC3: Đã đặt, chưa review → can_review=True."""
        res = logged_in_client.get(f"/api/can-review/{sample_product.id}")
        data = res.get_json()
        assert data["can_review"] is True
        assert data["has_booked"] is True
        assert data["has_reviewed"] is False

    def test_can_review_already_reviewed(self, test_session, logged_in_client,
                                          sample_product, confirmed_booking, logged_in_user):
        """TC4: Đã review rồi → can_review=False, reason=already_reviewed."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="Hay lắm")
        test_session.add(r)
        test_session.commit()

        res = logged_in_client.get(f"/api/can-review/{sample_product.id}")
        data = res.get_json()
        assert data["can_review"] is False
        assert data["reason"] == "already_reviewed"