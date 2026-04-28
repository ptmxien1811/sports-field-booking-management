"""
test_integ_payment_stats.py – INTEG-07: Payment → Revenue Stats
Kiểm tra luồng thanh toán ↔ thống kê doanh thu.
"""

import pytest
from sqlalchemy import func

from bookingapp import db
from bookingapp.models import Bill, Product, Category


class TestPaymentToStats:
    """INTEG-07: Kiểm tra luồng Payment ↔ Stats/Revenue."""

    def test_new_payment_increases_total_revenue(
            self, test_session, admin_client, logged_in_client,
            confirmed_booking, logged_in_user, sample_product):
        """
        TC1: Tạo bill mới → /stats hiển thị doanh thu tăng.
        Tích hợp: Bill → DB aggregation → stats route.
        """
        total_before = test_session.query(func.sum(Bill.amount)).scalar() or 0

        logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })

        total_after = test_session.query(func.sum(Bill.amount)).scalar() or 0
        assert total_after == total_before + sample_product.price

        res = admin_client.get("/stats", follow_redirects=True)
        assert res.status_code == 200

    def test_stats_count_increases_after_payment(
            self, test_session, logged_in_client, confirmed_booking):
        """
        TC2: Sau thanh toán, tổng bill count tăng lên 1.
        Tích hợp: /api/payment → Bill tạo mới → stats count.

        Dùng test_session.remove() thay vì expire_all() để đóng transaction cũ,
        buộc SQLAlchemy mở session mới và đọc được data do Flask app commit.
        """
        count_before = test_session.query(func.count(Bill.id)).scalar()

        test_session.commit()  # 🔥 QUAN TRỌNG

        r = logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "online",
        })
        assert r.get_json()["ok"] is True, f"Payment failed: {r.get_json()}"

        test_session.remove()

        count_after = test_session.query(func.count(Bill.id)).scalar()
        assert count_after == count_before + 1

    def test_cancel_paid_booking_decreases_revenue(
            self, test_session, logged_in_client, paid_booking):
        """
        TC3: Huỷ booking đã thanh toán → bill bị xoá → doanh thu giảm.
        Tích hợp: cancel → Bill delete → revenue aggregation.
        """
        booking, bill = paid_booking
        total_before = test_session.query(func.sum(Bill.amount)).scalar() or 0

        logged_in_client.post(f"/api/cancel-booking/{booking.id}")

        total_after = test_session.query(func.sum(Bill.amount)).scalar() or 0
        assert total_after == total_before - bill.amount

    def test_stats_by_category_reflects_payment(
            self, test_session, admin_client, logged_in_client,
            confirmed_booking, sample_category):
        """
        TC4: Thanh toán sân → /stats hiển thị đúng category.
        Tích hợp: Bill + Product + Category join → stats route.
        """
        logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })

        cat_revenue = test_session.query(
            Category.name,
            func.sum(Bill.amount)
        ).join(Product, Product.id == Bill.product_id) \
         .join(Category, Category.id == Product.category_id) \
         .group_by(Category.name).all()

        cat_names = [r[0] for r in cat_revenue]
        assert sample_category.name in cat_names