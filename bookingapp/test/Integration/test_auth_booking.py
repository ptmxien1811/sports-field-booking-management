"""
test_integ_auth_booking.py – INTEG-02: Auth → Booking
Kiểm tra luồng đăng nhập ↔ đặt sân.
"""

import pytest
from bookingapp.models import Booking, User


class TestAuthToBooking:
    """INTEG-02: Kiểm tra luồng Auth ↔ Booking."""

    def test_unauthenticated_cannot_book(self, test_client, product_with_slots, future_date):
        """
        TC1: Guest (chưa đăng nhập) POST /api/book → 401.
        Kiểm tra: middleware auth → booking bị chặn.
        """
        res = test_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        assert res.status_code == 401
        assert res.get_json()["ok"] is False

    def test_authenticated_can_book(self, logged_in_client, product_with_slots, future_date):
        """
        TC2: Đăng nhập xong POST /api/book → đặt thành công.
        Tích hợp: session → booking route → dao.create_booking → DB.
        """
        res = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        data = res.get_json()
        assert res.status_code == 200
        assert data["ok"] is True
        assert len(data["booking_ids"]) >= 1

        b = Booking.query.get(data["booking_ids"][0])
        assert b is not None
        assert b.status == "confirmed"

    def test_booking_saved_with_correct_user(self, logged_in_client, logged_in_user,
                                              product_with_slots, future_date):
        """
        TC3: Booking được lưu đúng user_id từ session.
        Tích hợp: session.user_id → booking.user_id trong DB.
        """
        res = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "09:00 - 10:00",
            "date": str(future_date),
        })
        bid = res.get_json()["booking_ids"][0]
        b = Booking.query.get(bid)
        assert b.user_id == logged_in_user.id

    def test_my_bookings_api_reflects_new_booking(self, logged_in_client,
                                                    product_with_slots, future_date):
        """
        TC4: Sau khi đặt, /api/my-bookings trả về số lượng tăng.
        Tích hợp: create_booking → get_bookings_by_user → API response.
        """
        res_before = logged_in_client.get("/api/my-bookings")
        count_before = res_before.get_json()["bookings"]

        logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "10:00 - 11:00",
            "date": str(future_date),
        })

        res_after = logged_in_client.get("/api/my-bookings")
        count_after = res_after.get_json()["bookings"]
        assert count_after == count_before + 1

    def test_two_users_book_different_slots_same_product(
            self, test_session, logged_in_client, second_client,
            product_with_slots, future_date, second_user):
        """
        TC5: Hai user đặt khác slot cùng sân → cả hai thành công.
        Tích hợp: isolation giữa 2 user session.
        """
        r1 = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        with second_client.session_transaction() as sess:
            sess["user_id"] = second_user.id
            sess["username"] = second_user.username

        r2 = second_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "09:00 - 10:00",
            "date": str(future_date),
        })

        assert r1.get_json()["ok"] is True
        assert r2.get_json()["ok"] is True

    def test_same_slot_conflict_between_users(
            self, test_session, logged_in_client, second_client,
            product_with_slots, future_date, second_user):
        """
        TC6: Hai user đặt CÙNG slot cùng sân → user 2 bị từ chối.
        Tích hợp: conflict detection trong dao.create_booking.
        """
        logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "14:00 - 15:00",
            "date": str(future_date),
        })

        with second_client.session_transaction() as sess:
            sess["user_id"] = second_user.id
            sess["username"] = second_user.username

        r2 = second_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "14:00 - 15:00",
            "date": str(future_date),
        })
        assert r2.get_json()["ok"] is False