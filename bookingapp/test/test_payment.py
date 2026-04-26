"""
test_payment.py – Kiểm thử chức năng Thanh Toán (Payment)
Module: CR200-PAYMENT | Dev: Long
Covers: Unit test (DB/Model), API test, Integration
"""

import pytest
import json
from flask import Flask
from datetime import datetime, timedelta
import bookingapp
from bookingapp import db
from bookingapp.models import User, Category, Product, Booking, Bill

# ─── Monkey-patch: đảm bảo routes đăng ký đúng app test ─────────────────────

if not hasattr(bookingapp, '_test_app_patched'):
    _app = Flask('bookingapp')
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    _app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    _app.config["TESTING"] = True
    _app.config["WTF_CSRF_ENABLED"] = False
    _app.secret_key = "test_secret_key_for_testing_only"

    bookingapp.app = _app
    bookingapp.db = db
    db.init_app(_app)

    with _app.app_context():
        from bookingapp import models, admin, index
        db.create_all()

    bookingapp._test_app_patched = True
else:
    _app = bookingapp.app

# ─── Import fixtures từ test_base ────────────────────────────────────────────
from bookingapp.test.test_base import (
    test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking, paid_booking,
)


@pytest.fixture(scope="function")
def test_app():
    """Override test_app: dùng app đã monkey-patch."""
    with _app.app_context():
        db.create_all()
        yield _app
        db.session.remove()
        db.drop_all()


# ─── Fixtures bổ sung ────────────────────────────────────────────────────────

@pytest.fixture
def another_user(test_session):
    """User khác (để test quyền truy cập)."""
    u = User(username="pay_other", email="payother@ex.com",
             phone="0978888888", auth_type="local")
    u.set_password("Other@1234")
    test_session.add(u)
    test_session.commit()
    return u


@pytest.fixture
def another_logged_in_client(test_client, another_user):
    """Client đăng nhập user khác."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = another_user.id
        sess["username"] = another_user.username
    return test_client


@pytest.fixture
def sample_product(test_session, sample_category):
    """Override: Product mẫu có image (cần cho template payment.html)."""
    from bookingapp.models import TimeSlot
    p = Product(
        name="Sân Mini A",
        price=300_000,
        category_id=sample_category.id,
        address="123 Đường Test, TP.HCM",
        phone="0901234567",
        active=True,
        image="test.jpg",
    )
    test_session.add(p)
    test_session.commit()
    for label in ["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00"]:
        ts = TimeSlot(product_id=p.id, label=label, period="morning")
        test_session.add(ts)
    test_session.commit()
    return p


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – MODEL / DB BILL
# ═══════════════════════════════════════════════════════════════════

class TestBillModel:
    """TC-PAY-MODEL: Kiểm tra tạo và ràng buộc Bill trong DB."""

    def test_bill_creation(self, test_session, confirmed_booking,
                           logged_in_user, sample_product):
        """TC1: Tạo Bill thành công với đầy đủ thông tin."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
            payment_method="direct",
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.id > 0

    def test_bill_amount_matches_product_price(self, test_session, confirmed_booking,
                                                logged_in_user, sample_product):
        """TC2: amount của Bill = price của Product."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
            payment_method="direct",
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.amount == sample_product.price

    def test_bill_default_payment_method(self, test_session, confirmed_booking,
                                          logged_in_user, sample_product):
        """TC3: payment_method default là 'direct'."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.payment_method == "direct"

    def test_bill_online_payment_method(self, test_session, confirmed_booking,
                                         logged_in_user, sample_product):
        """TC4: payment_method = 'online' được lưu đúng."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
            payment_method="online",
        )
        test_session.add(bill)
        test_session.commit()
        b = test_session.get(Bill, bill.id)
        assert b.payment_method == "online"

    def test_bill_str(self, test_session, confirmed_booking,
                      logged_in_user, sample_product):
        """TC5: __str__ Bill đúng format."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
        )
        test_session.add(bill)
        test_session.commit()
        assert f"#{bill.id}" in str(bill)
        assert "300000" in str(bill)

    def test_bill_created_at_auto(self, test_session, confirmed_booking,
                                   logged_in_user, sample_product):
        """TC6: created_at được tự động set."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.created_at is not None

    def test_bill_relationships(self, test_session, confirmed_booking,
                                 logged_in_user, sample_product):
        """TC7: Bill có quan hệ đúng với User, Product, Booking."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
        )
        test_session.add(bill)
        test_session.commit()
        b = test_session.get(Bill, bill.id)
        assert b.user.id == logged_in_user.id
        assert b.product.id == sample_product.id
        assert b.booking.id == confirmed_booking.id

    def test_booking_marked_paid_via_bill(self, test_session, confirmed_booking,
                                           logged_in_user, sample_product):
        """TC8: Kiểm tra booking đã thanh toán qua việc tìm Bill."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
        )
        test_session.add(bill)
        test_session.commit()
        existing = Bill.query.filter_by(booking_id=confirmed_booking.id).first()
        assert existing is not None


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: API/UI TEST – TRANG THANH TOÁN /payment/<id>
# ═══════════════════════════════════════════════════════════════════

class TestPaymentPage:
    """TC-PAY-PAGE: Kiểm tra truy cập trang thanh toán."""

    def test_payment_page_accessible(self, logged_in_client, confirmed_booking):
        """TC1: Người dùng đăng nhập truy cập trang thanh toán → 200."""
        res = logged_in_client.get(
            f"/payment/{confirmed_booking.id}", follow_redirects=True
        )
        assert res.status_code == 200

    def test_payment_page_unauthenticated_redirect(self, test_client, confirmed_booking):
        """TC2: Chưa đăng nhập → redirect login."""
        res = test_client.get(
            f"/payment/{confirmed_booking.id}", follow_redirects=False
        )
        assert res.status_code == 302

    def test_payment_page_wrong_user(self, another_logged_in_client, confirmed_booking):
        """TC3: User khác truy cập trang thanh toán → redirect."""
        res = another_logged_in_client.get(
            f"/payment/{confirmed_booking.id}", follow_redirects=False
        )
        assert res.status_code == 302

    def test_payment_page_nonexistent_booking(self, logged_in_client):
        """TC4: Booking không tồn tại → redirect."""
        res = logged_in_client.get("/payment/99999", follow_redirects=False)
        assert res.status_code == 302

    def test_payment_page_already_paid(self, logged_in_client, paid_booking):
        """TC5: Trang thanh toán khi booking đã trả → vẫn render (200)."""
        booking_obj, bill = paid_booking
        res = logged_in_client.get(
            f"/payment/{booking_obj.id}", follow_redirects=True
        )
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: API TEST – XỬ LÝ THANH TOÁN POST /api/payment
# ═══════════════════════════════════════════════════════════════════

class TestPaymentAPI:
    """TC-PAY-API: Kiểm tra API thanh toán."""

    def _post_payment(self, client, booking_id, method="direct"):
        """Helper: gọi POST /api/payment."""
        return client.post(
            "/api/payment",
            data=json.dumps({"booking_id": booking_id, "payment_method": method}),
            content_type="application/json",
        )

    def test_payment_success_direct(self, logged_in_client, confirmed_booking):
        """TC1: Thanh toán trực tiếp thành công → 200 ok=True."""
        res = self._post_payment(logged_in_client, confirmed_booking.id, "direct")
        data = json.loads(res.data)
        assert res.status_code == 200
        assert data["ok"] is True
        assert "bill_id" in data

    def test_payment_success_online(self, logged_in_client, confirmed_booking):
        """TC2: Thanh toán online thành công."""
        res = self._post_payment(logged_in_client, confirmed_booking.id, "online")
        data = json.loads(res.data)
        assert data["ok"] is True

    def test_payment_creates_bill_in_db(self, logged_in_client, confirmed_booking):
        """TC3: Sau thanh toán, Bill xuất hiện trong DB."""
        self._post_payment(logged_in_client, confirmed_booking.id, "direct")
        bill = Bill.query.filter_by(booking_id=confirmed_booking.id).first()
        assert bill is not None

    def test_payment_duplicate_rejected(self, logged_in_client, paid_booking):
        """TC4: Thanh toán 2 lần → lần 2 bị từ chối (400)."""
        booking_obj, _ = paid_booking
        res = self._post_payment(logged_in_client, booking_obj.id, "direct")
        data = json.loads(res.data)
        assert data["ok"] is False
        assert res.status_code == 400

    def test_payment_unauthenticated(self, test_client, confirmed_booking):
        """TC5: Chưa đăng nhập → 401."""
        res = self._post_payment(test_client, confirmed_booking.id, "direct")
        assert res.status_code == 401

    def test_payment_wrong_user(self, another_logged_in_client, confirmed_booking):
        """TC6: User khác cố thanh toán → 404."""
        res = self._post_payment(another_logged_in_client, confirmed_booking.id, "direct")
        data = json.loads(res.data)
        assert data["ok"] is False

    def test_payment_nonexistent_booking(self, logged_in_client):
        """TC7: Booking không tồn tại → 404."""
        res = self._post_payment(logged_in_client, 99999, "direct")
        assert res.status_code == 404

    def test_payment_bill_amount_correct(self, logged_in_client, confirmed_booking,
                                          sample_product):
        """TC8: Bill amount = giá sân."""
        self._post_payment(logged_in_client, confirmed_booking.id, "direct")
        bill = Bill.query.filter_by(booking_id=confirmed_booking.id).first()
        assert bill.amount == sample_product.price

    def test_payment_response_has_bill_id(self, logged_in_client, confirmed_booking):
        """TC9: Response thanh toán có bill_id (int)."""
        res = self._post_payment(logged_in_client, confirmed_booking.id, "direct")
        data = json.loads(res.data)
        assert isinstance(data.get("bill_id"), int)

    def test_payment_response_message(self, logged_in_client, confirmed_booking):
        """TC10: Response có msg hợp lệ."""
        res = self._post_payment(logged_in_client, confirmed_booking.id, "direct")
        data = json.loads(res.data)
        assert "msg" in data
        assert len(data["msg"]) > 0


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: INTEGRATION TEST
# ═══════════════════════════════════════════════════════════════════

class TestPaymentIntegration:
    """TC-PAY-INTEG: Kiểm tra luồng thanh toán đầy đủ."""

    def test_payment_flow_complete(self, logged_in_client, confirmed_booking,
                                    sample_product):
        """TC1: Luồng đầy đủ: book → pay → kiểm tra bill."""
        booking_id = confirmed_booking.id

        # Bước 1: Chưa có bill
        bill_before = Bill.query.filter_by(booking_id=booking_id).first()
        assert bill_before is None

        # Bước 2: Thanh toán
        res = logged_in_client.post(
            "/api/payment",
            data=json.dumps({"booking_id": booking_id, "payment_method": "direct"}),
            content_type="application/json",
        )
        data = json.loads(res.data)
        assert data["ok"] is True

        # Bước 3: Bill đã tồn tại
        bill_after = Bill.query.filter_by(booking_id=booking_id).first()
        assert bill_after is not None

    def test_paid_booking_shows_on_home(self, logged_in_client, paid_booking):
        """TC2: Trang chủ hiển thị booking đã thanh toán."""
        res = logged_in_client.get("/", follow_redirects=True)
        assert res.status_code == 200

    def test_bill_persists_after_expire(self, test_session, confirmed_booking,
                                         logged_in_user, sample_product):
        """TC3: Bill tồn tại bền vững sau commit + expire."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
        )
        test_session.add(bill)
        test_session.commit()
        bill_id = bill.id

        test_session.expire_all()
        b = test_session.get(Bill, bill_id)
        assert b is not None
        assert b.amount == sample_product.price
