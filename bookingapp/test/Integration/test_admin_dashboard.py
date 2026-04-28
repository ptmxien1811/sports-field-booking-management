"""
test_integ_admin_dashboard.py – INTEG-08: Admin Dashboard
Kiểm tra tích hợp admin dashboard với dữ liệu thật.

LƯU Ý: Các test /admin/ phải dùng admin_app (app có Flask-Admin đăng ký),
        không dùng test_app thông thường (sẽ trả về 404 cho /admin/).
"""

import pytest
from datetime import datetime, timedelta

from bookingapp import db
from bookingapp.models import Booking, Bill

# ── Import admin_app để có Flask-Admin routes ─────────────────────────────────
from bookingapp.test.test_base import (
    admin_app,
    sample_category, sample_product,
    logged_in_user, admin_user,
)


# ── Fixtures override dùng admin_app ─────────────────────────────────────────

@pytest.fixture
def adm_session(admin_app):
    with admin_app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def adm_admin_client(admin_app, admin_user):
    """Admin client dùng admin_app (có /admin/ route)."""
    client = admin_app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.id
        sess["username"] = "admin"
    return client


@pytest.fixture
def adm_normal_client(admin_app, logged_in_user):
    """Normal user client dùng admin_app."""
    client = admin_app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = logged_in_user.id
        sess["username"] = logged_in_user.username
    return client


class TestAdminDashboardIntegration:
    """INTEG-08: Kiểm tra tích hợp Admin dashboard."""

    def test_admin_dashboard_stats_after_data_creation(
            self, adm_session, adm_admin_client, logged_in_user, sample_product):
        """
        TC1: Admin dashboard render thành công khi có đủ dữ liệu (bill có amount > 0).
        Tích hợp: Bill seeded → stats query → home-admin.html render.

        Vì adm_session và Flask app request dùng cùng SQLite in-memory DB,
        ta dùng scoped_session nên cần remove() để Flask thấy commit mới nhất.
        """
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            amount=sample_product.price,
            payment_method="direct",
        )
        adm_session.add(bill)
        adm_session.commit()
        # Release scoped session để Flask app request tạo session mới đọc đúng data
        adm_session.remove()

        res = adm_admin_client.get("/admin/", follow_redirects=True)
        assert res.status_code == 200
        assert len(res.data) > 100

    def test_non_admin_blocked_from_admin_panel(self, adm_normal_client):
        """
        TC2: User thường truy cập /admin/ → bị redirect (302) hoặc forbidden (403).
        Tích hợp: admin access control → redirect.
        """
        res = adm_normal_client.get("/admin/", follow_redirects=False)
        assert res.status_code in [302, 403]

    def test_admin_can_view_all_bookings_via_dao(
            self, adm_session, adm_admin_client, logged_in_user, sample_product):
        """
        TC3: Admin gọi get_all_bookings → thấy booking của mọi user.
        Tích hợp: dao.get_all_bookings → admin dashboard.
        """
        from bookingapp.dao import get_all_bookings
        future = datetime.now() + timedelta(days=1)
        day_start = future.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="09:00 - 10:00",
            date=day_start,
            start_time=future.replace(hour=9),
            end_time=future.replace(hour=10),
            status="confirmed",
        )
        adm_session.add(b)
        adm_session.commit()

        all_bookings = get_all_bookings()
        assert any(item["username"] == logged_in_user.username for item in all_bookings)

    def test_admin_stats_route_with_date_filter(self, adm_session, adm_admin_client,
                                                 logged_in_user, sample_product):
        """
        TC4: /stats?start_date=...&end_date=... không crash khi có bills.
        Tích hợp: stats route với filter + Bill query.
        """
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            amount=100_000,
            payment_method="direct",
        )
        adm_session.add(bill)
        adm_session.commit()

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        res = adm_admin_client.get(f"/stats?start_date={yesterday}&end_date={today}")
        assert res.status_code == 200