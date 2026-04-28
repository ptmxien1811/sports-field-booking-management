"""
test_integ_booking_payment.py – INTEG-03: Booking → Payment
Kiểm tra luồng đặt sân ↔ thanh toán.
"""

import pytest
from bookingapp.models import Bill, User


class TestBookingToPayment:
    """INTEG-03: Kiểm tra luồng Booking ↔ Payment."""

    def test_book_then_pay_creates_bill(self, logged_in_client,
                                         product_with_slots, future_date):
        """
        TC1: Đặt sân → thanh toán → bill tồn tại trong DB.
        Tích hợp: /api/book → /api/payment → Bill model.
        """
        r_book = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        booking_id = r_book.get_json()["booking_ids"][0]

        r_pay = logged_in_client.post("/api/payment", json={
            "booking_id": booking_id,
            "payment_method": "direct",
        })
        pay_data = r_pay.get_json()
        assert r_pay.status_code == 200
        assert pay_data["ok"] is True

        bill = Bill.query.filter_by(booking_id=booking_id).first()
        assert bill is not None
        assert bill.amount == product_with_slots.price

    def test_pay_twice_same_booking_rejected(self, logged_in_client, confirmed_booking):
        """
        TC2: Thanh toán lần 2 cùng booking → bị từ chối (400).
        Tích hợp: Bill.query.filter_by(booking_id) check → 400 response.
        """
        logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })
        r2 = logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })
        assert r2.status_code == 400
        assert r2.get_json()["ok"] is False

    def test_payment_page_shows_booking_info(self, logged_in_client, confirmed_booking):
        """
        TC3: Trang /payment/<id> hiển thị thông tin đặt sân.
        Tích hợp: Booking → Payment template rendering.
        """
        res = logged_in_client.get(f"/payment/{confirmed_booking.id}")
        assert res.status_code == 200

    def test_other_user_cannot_pay_booking(self, test_session, test_client,
                                             confirmed_booking):
        """
        TC4: User khác không thể thanh toán booking của người khác.
        Tích hợp: session.user_id vs booking.user_id check.
        """
        other = User(username="other_pay_integ", auth_type="local")
        other.set_password("Test@1234")
        test_session.add(other)
        test_session.commit()

        with test_client.session_transaction() as sess:
            sess["user_id"] = other.id
            sess["username"] = other.username

        r = test_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })
        assert r.get_json()["ok"] is False

    def test_bill_amount_equals_product_price_times_slots(
            self, logged_in_client, product_with_slots, future_date):
        """
        TC5: Bill amount = price × số slot đặt khi đặt nhiều slot cùng lúc.
        Tích hợp: multi-slot booking → payment amount calculation.
        """
        r_book = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slots": ["08:00 - 09:00", "09:00 - 10:00"],
            "date": str(future_date),
        })
        booking_ids = r_book.get_json()["booking_ids"]
        assert len(booking_ids) == 2

        r_pay = logged_in_client.post("/api/payment", json={
            "booking_id": booking_ids[0],
            "payment_method": "online",
        })
        assert r_pay.get_json()["ok"] is True

        bill = Bill.query.filter_by(booking_id=booking_ids[0]).first()
        assert bill.amount == product_with_slots.price * 2