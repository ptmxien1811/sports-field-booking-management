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
        slots = ["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00"]
        booked_ids = []
        for s in slots:
            b, _ = create_booking(logged_in_user.id, product_with_slots.id, s, future_date)
            booked_ids.append(b.id)

        _, err = create_booking(logged_in_user.id, product_with_slots.id,
                                 "14:00 - 15:00", future_date)
        assert err is not None

        cancel_booking_by_id(booked_ids[0], logged_in_user.id)

        b_new, err_new = create_booking(logged_in_user.id, product_with_slots.id,
                                         "14:00 - 15:00", future_date)
        assert err_new is None
        assert b_new.status == "confirmed"

    def test_cancel_nonexistent_booking_safe(self, logged_in_client):
        """
        TC4: Huỷ booking không tồn tại → redirect an toàn, không crash.
        Tích hợp: cancel route → dao → graceful 302.
        """
        res = logged_in_client.post("/api/cancel-booking/999999",
                                     follow_redirects=False)
        assert res.status_code == 302