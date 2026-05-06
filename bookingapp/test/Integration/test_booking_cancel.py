"""
test_integ_booking_cancel.py – INTEG-04: Booking → Cancel → Hoàn tiền
Kiểm tra luồng huỷ đặt sân và hoàn tiền.
"""

import pytest
from datetime import datetime, timedelta

from bookingapp.models import Booking, Bill
from bookingapp.dao import create_booking, cancel_booking_by_id


class TestBookingToCancelRefund:
    """INTEG-04: Kiểm tra luồng Booking → Cancel → Hoàn tiền."""

    def test_cancel_removes_bill_refund(self, test_session, logged_in_client,
                                         logged_in_user, paid_booking):
        """
        TC1: Huỷ sân đã thanh toán → bill bị xoá (hoàn tiền).
        Tích hợp: cancel_booking_by_id → Bill.delete → DB.
        """
        booking, bill = paid_booking
        bill_id = bill.id

        res = logged_in_client.post(f"/api/cancel-booking/{booking.id}",
                                     follow_redirects=False)
        assert res.status_code == 302

        assert Bill.query.get(bill_id) is None
        b = Booking.query.get(booking.id)
        assert b.status == "cancelled"

    def test_slot_freed_after_cancel_allows_rebook(
            self, test_session, logged_in_client, product_with_slots,
            logged_in_user, future_date):
        """
        TC2: Huỷ booking → slot được giải phóng → user khác đặt được.
        Tích hợp: cancel_booking_by_id → TimeSlot.active=True → create_booking.
        """
        r1 = logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })
        booking_id = r1.get_json()["booking_ids"][0]

        logged_in_client.post(f"/api/cancel-booking/{booking_id}")
        b = Booking.query.get(booking_id)
        assert b.status == "cancelled"

        b2, err = create_booking(logged_in_user.id, product_with_slots.id,
                                  "08:00 - 09:00", future_date)
        assert err is None
        assert b2.status == "confirmed"

    def test_cancel_updates_daily_booking_count(
            self, test_session, logged_in_client, logged_in_user,
            product_with_slots, future_date):
        """
        TC3: Sau huỷ, bộ đếm booking trong ngày giảm → cho phép đặt thêm.
        Tích hợp: cancel → count check trong create_booking.
        """
        from bookingapp.models import Category, Product

        # Tạo thêm 2 sân phụ để đủ 3 sân khác nhau
        cat = test_session.query(Category).first()
        product_b = Product(name="Sân Phụ B", price=100000, category_id=cat.id, active=True)
        product_c = Product(name="Sân Phụ C", price=100000, category_id=cat.id, active=True)
        product_d = Product(name="Sân Phụ D", price=100000, category_id=cat.id, active=True)
        test_session.add_all([product_b, product_c, product_d])
        test_session.commit()

        # Đặt 3 sân khác nhau → đạt giới hạn
        b1, _ = create_booking(logged_in_user.id, product_with_slots.id, "08:00 - 09:00", future_date)
        b2, _ = create_booking(logged_in_user.id, product_b.id, "08:00 - 09:00", future_date)
        b3, _ = create_booking(logged_in_user.id, product_c.id, "08:00 - 09:00", future_date)

        # Thử đặt sân thứ 4 (sân D) → phải bị chặn
        _, err = create_booking(logged_in_user.id, product_d.id, "08:00 - 09:00", future_date)
        assert err is not None, "Phải bị chặn khi đã đặt 3 sân khác nhau"

        # Hủy sân B
        cancel_booking_by_id(b2.id, logged_in_user.id)

        # Sau khi hủy → đặt sân D phải thành công
        b_new, err_new = create_booking(logged_in_user.id, product_d.id, "08:00 - 09:00", future_date)
        assert err_new is None, f"Phải đặt được sau khi hủy: {err_new}"
        assert b_new.status == "confirmed"
    def test_cancel_nonexistent_booking_safe(self, logged_in_client):
        """
        TC4: Huỷ booking không tồn tại → redirect an toàn, không crash.
        Tích hợp: cancel route → dao → graceful 302.
        """
        res = logged_in_client.post("/api/cancel-booking/999999",
                                     follow_redirects=False)
        assert res.status_code == 302