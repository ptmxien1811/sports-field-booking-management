"""
test_integ_full_journey.py – INTEG-09: Full User Journey (End-to-End)
Luồng hoàn chỉnh từ đăng ký đến thanh toán và review.
"""

import pytest
from datetime import datetime, timedelta

from bookingapp.models import User, Booking, Bill, Review, Favorite
from bookingapp.dao import create_booking


class TestFullUserJourney:
    """INTEG-09: Luồng hoàn chỉnh từ đăng ký đến thanh toán và review."""

    def test_complete_booking_journey(self, test_client, product_with_slots):
        """
        TC1: Đăng ký → Login → Đặt sân → Thanh toán → Kiểm tra Bill → Review.
        Luồng end-to-end toàn bộ hệ thống.
        """
        # ── Bước 1: Đăng ký ──────────────────────────────────────────────────
        res_reg = test_client.post("/register", data={
            "username": "journey_user",
            "password": "Journey@123",
            "confirm_password": "Journey@123",
            "email": "journey@test.com",
            "phone": "0966777888",
        }, follow_redirects=True)
        assert res_reg.status_code == 200
        user = User.query.filter_by(username="journey_user").first()
        assert user is not None

        # ── Bước 2: Kiểm tra session ───────────────────────────────────────────
        with test_client.session_transaction() as sess:
            assert sess.get("user_id") == user.id

        # ── Bước 3: Đặt sân ──────────────────────────────────────────────────
        future = (datetime.now() + timedelta(days=2)).date()
        r_book = test_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future),
        })
        assert r_book.status_code == 200
        booking_id = r_book.get_json()["booking_ids"][0]
        booking = Booking.query.get(booking_id)
        assert booking.status == "confirmed"
        assert booking.user_id == user.id

        # ── Bước 4: Thanh toán ────────────────────────────────────────────────
        r_pay = test_client.post("/api/payment", json={
            "booking_id": booking_id,
            "payment_method": "direct",
        })
        assert r_pay.status_code == 200
        assert r_pay.get_json()["ok"] is True
        bill = Bill.query.filter_by(booking_id=booking_id).first()
        assert bill is not None
        assert bill.user_id == user.id

        # ── Bước 5: Review sân ────────────────────────────────────────────────
        r_review = test_client.post(f"/api/review/{product_with_slots.id}", json={
            "rating": 5,
            "content": "Trải nghiệm tuyệt vời!",
        })
        assert r_review.status_code == 200
        assert r_review.get_json()["ok"] is True
        review = Review.query.filter_by(product_id=product_with_slots.id,
                                         user_id=user.id).first()
        assert review is not None
        assert review.rating == 5

        # ── Bước 6: Kiểm tra trang venue ─────────────────────────────────────
        r_venue = test_client.get(f"/venue/{product_with_slots.id}")
        assert r_venue.status_code == 200

    def test_book_pay_cancel_rebook_journey(
            self, test_session, logged_in_client, logged_in_user,
            product_with_slots, future_date):
        """
        TC2: Đặt → Thanh toán → Huỷ (hoàn tiền) → Đặt lại → Thành công.
        """
        # Đặt
        r1 = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        booking_id = r1.get_json()["booking_ids"][0]

        # Thanh toán
        logged_in_client.post("/api/payment", json={
            "booking_id": booking_id,
            "payment_method": "direct",
        })
        bill = Bill.query.filter_by(booking_id=booking_id).first()
        assert bill is not None

        # Huỷ → bill xoá
        logged_in_client.post(f"/api/cancel-booking/{booking_id}")
        assert Bill.query.filter_by(booking_id=booking_id).first() is None
        assert Booking.query.get(booking_id).status == "cancelled"

        # Đặt lại cùng slot
        b2, err = create_booking(logged_in_user.id, product_with_slots.id,
                                  "08:00 - 09:00", future_date)
        assert err is None
        assert b2.status == "confirmed"

    def test_favorite_and_book_same_venue(
            self, logged_in_client, product_with_slots, future_date):
        """
        TC3: Yêu thích sân → đặt sân đó → cả hai tồn tại độc lập trong DB.
        Tích hợp: Favorite + Booking không ảnh hưởng nhau.
        """
        r_fav = logged_in_client.post(f"/api/favorite/{product_with_slots.id}")
        assert r_fav.get_json()["added"] is True

        r_book = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        assert r_book.get_json()["ok"] is True

        fav_count = logged_in_client.get("/api/my-favorites").get_json()["favorites"]
        book_count = logged_in_client.get("/api/my-bookings").get_json()["bookings"]
        assert fav_count == 1
        assert book_count == 1