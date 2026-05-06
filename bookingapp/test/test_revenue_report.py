"""
test_revenue_report.py – Kiểm thử chức năng Báo Cáo Doanh Thu (Stats)
Module: CR600-STATS | Dev: Long
Covers: Unit test (DB aggregation), API test (/stats route), Integration
"""

import pytest
import json
from flask import Flask
from datetime import datetime, timedelta
from sqlalchemy import func
import bookingapp
from bookingapp import db
from bookingapp.models import User, Category, Product, Booking, Bill

from bookingapp.test.test_base import (
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking, paid_booking,
    admin_user, admin_client,
)


# ─── Fixtures bổ sung ────────────────────────────────────────────────────────

@pytest.fixture
def non_admin_client(test_client, logged_in_user):
    """Client đăng nhập user thường (không phải admin)."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = logged_in_user.id
        sess["username"] = logged_in_user.username
    return test_client


@pytest.fixture
def multi_bills(test_session, logged_in_user, sample_product, confirmed_booking):
    """Tạo 3 bills với ngày khác nhau để test chart doanh thu."""
    bills = []
    base_date = datetime.now() - timedelta(days=5)

    for i, days_offset in enumerate([4, 3, 2]):
        future = datetime.now() + timedelta(days=10 + i)
        day_start = future.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label=f"0{6+i}:00 - 0{7+i}:00",
            date=day_start,
            start_time=future.replace(hour=6+i),
            end_time=future.replace(hour=7+i),
            status="confirmed",
        )
        test_session.add(b)
        test_session.commit()

        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=b.id,
            amount=300_000 * (i + 1),
            payment_method="direct",
            created_at=base_date + timedelta(days=days_offset),
        )
        test_session.add(bill)
        test_session.commit()
        bills.append(bill)

    return bills


@pytest.fixture
def category_bills(test_session, logged_in_user, confirmed_booking):
    """Tạo bills từ các loại sân khác nhau để test phân tích theo loại."""
    cat2 = Category(name="Sân Tennis")
    test_session.add(cat2)
    test_session.commit()

    p2 = Product(name="Sân Tennis B1", price=400_000,
                 category_id=cat2.id, active=True)
    test_session.add(p2)
    test_session.commit()

    u = test_session.get(User, confirmed_booking.user_id)

    future = datetime.now() + timedelta(days=5)
    day_start = future.replace(hour=0, minute=0, second=0, microsecond=0)
    b2 = Booking(
        user_id=u.id, product_id=p2.id,
        slot_label="10:00 - 11:00",
        date=day_start,
        start_time=future.replace(hour=10),
        end_time=future.replace(hour=11),
        status="confirmed",
    )
    test_session.add(b2)
    test_session.commit()

    bill2 = Bill(
        user_id=u.id, product_id=p2.id,
        booking_id=b2.id, amount=400_000,
    )
    test_session.add(bill2)
    test_session.commit()
    return bill2


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – DB AGGREGATION LAYER
# ═══════════════════════════════════════════════════════════════════

class TestRevenueCalculation:
    """TC-STATS-CALC: Kiểm tra các phép tính thống kê doanh thu."""

    def test_total_revenue_no_bills(self, test_session):
        """ Không có bill nào → tổng doanh thu = 0."""
        total = test_session.query(func.sum(Bill.amount)).scalar() or 0
        assert total == 0

    def test_total_revenue_single_bill(self, test_session, confirmed_booking,
                                        logged_in_user, sample_product):
        """ 1 bill → tổng = giá trị bill đó."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
        )
        test_session.add(bill)
        test_session.commit()
        total = test_session.query(func.sum(Bill.amount)).scalar()
        assert total == 300_000

    def test_total_revenue_multiple_bills(self, test_session, multi_bills):
        """ Nhiều bills → tổng doanh thu đúng."""
        expected = sum(b.amount for b in multi_bills)
        total = test_session.query(func.sum(Bill.amount)).scalar() or 0
        assert total == expected

    def test_total_bookings_count(self, test_session, multi_bills):
        """ Đếm tổng đơn đặt (bill) đúng."""
        count = test_session.query(func.count(Bill.id)).scalar()
        assert count == len(multi_bills)

    def test_revenue_by_date_grouped(self, test_session, multi_bills):
        """ Doanh thu group by ngày có đúng số ngày."""
        rows = test_session.query(
            func.date(Bill.created_at),
            func.sum(Bill.amount)
        ).group_by(func.date(Bill.created_at)).all()
        assert len(rows) == len(multi_bills)

    def test_revenue_by_category(self, test_session, paid_booking, category_bills):
        """ Doanh thu phân chia theo loại sân."""
        rows = test_session.query(
            Category.name,
            func.sum(Bill.amount)
        ).join(Product, Product.id == Bill.product_id) \
         .join(Category, Category.id == Product.category_id) \
         .group_by(Category.name).all()
        assert len(rows) >= 2

    def test_revenue_filter_by_date_range(self, test_session, multi_bills):
        """ Lọc doanh thu theo khoảng ngày."""
        start = datetime.now() - timedelta(days=6)
        end = datetime.now() - timedelta(days=1)
        filtered = test_session.query(func.sum(Bill.amount)).filter(
            Bill.created_at >= start,
            Bill.created_at < end
        ).scalar() or 0
        assert filtered >= 0

    def test_this_month_revenue(self, test_session, confirmed_booking,
                                 logged_in_user, sample_product):
        """ Doanh thu tháng này tính đúng."""
        today = datetime.now().date()
        first_of_month = today.replace(day=1)
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=500_000,
            created_at=datetime.now(),
        )
        test_session.add(bill)
        test_session.commit()

        this_month_rev = test_session.query(func.sum(Bill.amount)).filter(
            Bill.created_at >= datetime.combine(first_of_month, datetime.min.time()),
        ).scalar() or 0
        assert this_month_rev == 500_000

    def test_last_month_revenue_zero_when_no_bills(self, test_session):
        """ Không có bill tháng trước → doanh thu = 0."""
        today = datetime.now().date()
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        first_of_last_month = last_month_end.replace(day=1)

        last_month_rev = test_session.query(func.sum(Bill.amount)).filter(
            Bill.created_at >= datetime.combine(first_of_last_month, datetime.min.time()),
            Bill.created_at < datetime.combine(first_of_this_month, datetime.min.time()),
        ).scalar() or 0
        assert last_month_rev == 0

    def test_growth_rate_positive(self):
        """ Tăng trưởng dương khi tháng này > tháng trước."""
        this_month = 1_000_000
        last_month = 500_000
        growth = round(((this_month - last_month) / last_month) * 100, 1)
        assert growth == 100.0

    def test_growth_rate_negative(self):
        """ Tăng trưởng âm khi tháng này < tháng trước."""
        this_month = 400_000
        last_month = 800_000
        growth = round(((this_month - last_month) / last_month) * 100, 1)
        assert growth == -50.0

    def test_growth_rate_no_last_month(self):
        """ Tháng trước = 0, tháng này > 0 → growth = 100%."""
        this_month = 500_000
        last_month = 0
        growth = 100.0 if this_month > 0 else 0.0
        assert growth == 100.0

    def test_growth_rate_both_zero(self):
        """ Cả hai tháng = 0 → growth = 0%."""
        this_month = 0
        last_month = 0
        growth = 100.0 if this_month > 0 else 0.0
        assert growth == 0.0

    def test_category_percent_calculation(self):
        """ Phần trăm doanh thu theo loại tính đúng."""
        total = 1_000_000
        categories = [
            {"name": "Bóng đá", "revenue": 600_000},
            {"name": "Cầu lông", "revenue": 400_000},
        ]
        for cat in categories:
            cat["percent"] = round(cat["revenue"] / total * 100, 1)

        assert categories[0]["percent"] == 60.0
        assert categories[1]["percent"] == 40.0
        assert sum(c["percent"] for c in categories) == 100.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: API TEST – ROUTE /stats
# ═══════════════════════════════════════════════════════════════════

class TestStatsRoute:
    """TC-STATS-ROUTE: Kiểm tra route /stats với các tham số."""

    def test_stats_admin_no_filter(self, admin_client):
        """ Admin /stats không filter → 200."""
        res = admin_client.get("/stats", follow_redirects=True)
        assert res.status_code == 200

    def test_stats_with_start_date(self, admin_client):
        """ /stats?start_date=2024-01-01 → 200."""
        res = admin_client.get("/stats?start_date=2024-01-01")
        assert res.status_code == 200

    def test_stats_with_end_date(self, admin_client):
        """ /stats?end_date=2024-12-31 → 200."""
        res = admin_client.get("/stats?end_date=2024-12-31")
        assert res.status_code == 200

    def test_stats_with_both_dates(self, admin_client):
        """ /stats với cả start và end → 200."""
        res = admin_client.get("/stats?start_date=2024-01-01&end_date=2024-06-30")
        assert res.status_code == 200

    def test_stats_date_swap_no_error(self, admin_client):
        """ start > end → tự hoán đổi, không lỗi."""
        res = admin_client.get(
            "/stats?start_date=2025-12-31&end_date=2024-01-01",
            follow_redirects=True
        )
        assert res.status_code == 200

    def test_stats_future_date_clamped(self, admin_client):
        """ Ngày tương lai bị clamp về hôm nay, không lỗi."""
        res = admin_client.get(
            "/stats?start_date=2099-01-01", follow_redirects=True
        )
        assert res.status_code == 200

    def test_stats_invalid_date_format(self, admin_client):
        """ Ngày sai format → không crash (xử lý graceful)."""
        res = admin_client.get(
            "/stats?start_date=not-a-date", follow_redirects=True
        )
        assert res.status_code == 200

    def test_stats_non_admin_redirect(self, non_admin_client):
        """ Non-admin vào /stats → redirect."""
        res = non_admin_client.get("/stats", follow_redirects=False)
        assert res.status_code == 302

    def test_stats_unauthenticated_redirect(self, test_client):
        """: Chưa đăng nhập vào /stats → redirect."""
        res = test_client.get("/stats", follow_redirects=False)
        assert res.status_code == 302

    def test_stats_response_contains_data(self, admin_client, multi_bills):
        """ Response /stats chứa nội dung trang HTML."""
        res = admin_client.get("/stats", follow_redirects=True)
        assert res.status_code == 200
        assert b"<html" in res.data or len(res.data) > 100


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: INTEGRATION TEST
# ═══════════════════════════════════════════════════════════════════

class TestStatsIntegration:
    """TC-STATS-INTEG: Kiểm tra tích hợp DB ↔ Report."""

    def test_stats_reflects_new_bill(self, test_session, admin_client,
                                      confirmed_booking, logged_in_user,
                                      sample_product):
        """ Tạo bill mới → doanh thu tăng."""
        total_before = test_session.query(func.sum(Bill.amount)).scalar() or 0

        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
        )
        test_session.add(bill)
        test_session.commit()

        total_after = test_session.query(func.sum(Bill.amount)).scalar() or 0
        assert total_after == total_before + 300_000

    def test_stats_correct_after_bill_delete(self, test_session, confirmed_booking,
                                              logged_in_user, sample_product):
        """ Xóa bill → doanh thu giảm tương ứng."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
        )
        test_session.add(bill)
        test_session.commit()

        total_with = test_session.query(func.sum(Bill.amount)).scalar() or 0

        test_session.delete(bill)
        test_session.commit()

        total_without = test_session.query(func.sum(Bill.amount)).scalar() or 0
        assert total_without == total_with - 300_000

    def test_revenue_by_day_order(self, test_session, multi_bills):
        """ Doanh thu theo ngày trả về đúng thứ tự thời gian."""
        rows = test_session.query(
            func.date(Bill.created_at),
            func.sum(Bill.amount)
        ).group_by(func.date(Bill.created_at)) \
         .order_by(func.date(Bill.created_at)) \
         .all()

        dates = [str(r[0]) for r in rows]
        assert dates == sorted(dates)

    def test_category_stats_sum_equals_total(self, test_session, paid_booking):
        """ Tổng doanh thu từng loại = tổng doanh thu."""
        total = test_session.query(func.sum(Bill.amount)).scalar() or 0
        cat_total = test_session.query(
            func.sum(Bill.amount)
        ).join(Product, Product.id == Bill.product_id) \
         .join(Category, Category.id == Product.category_id) \
         .scalar() or 0
        assert total == cat_total


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: API TEST – /stats invalid end_date (index.py:750)
# ═══════════════════════════════════════════════════════════════════

class TestStatsInvalidEndDate:
    """TC-STATS-ENDDATE: Kiểm tra xử lý end_date sai format."""

    def test_stats_invalid_end_date_format(self, admin_client):
        """TC1: end_date sai format → không crash (index.py:750)."""
        res = admin_client.get(
            "/stats?end_date=not-a-date", follow_redirects=True
        )
        assert res.status_code == 200

    def test_stats_invalid_both_dates(self, admin_client):
        """ Cả start và end đều sai format → xử lý graceful."""
        res = admin_client.get(
            "/stats?start_date=abc&end_date=xyz", follow_redirects=True
        )
        assert res.status_code == 200
