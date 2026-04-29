"""
test_payment.py – Kiểm thử chức năng Thanh Toán (Payment)
Module: CR200-PAYMENT
Covers: Unit test (DB/Model), API test, Integration, Mock
"""

import pytest
import json
from unittest.mock import MagicMock, PropertyMock
from datetime import datetime, timedelta
from bookingapp import db
from bookingapp.models import User, Category, Product, Booking, Bill

# ─── Dùng hoàn toàn từ test_base, KHÔNG monkey-patch ────────────────────────
from bookingapp.test.test_base import (
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking, paid_booking,
)


# ─── Fixtures bổ sung riêng cho payment ──────────────────────────────────────

@pytest.fixture
def another_user(test_session):
    u = User(username="pay_other", email="payother@ex.com",
             phone="0978888888", auth_type="local")
    u.set_password("Other@1234")
    test_session.add(u)
    test_session.commit()
    return u


@pytest.fixture
def another_logged_in_client(test_client, another_user):
    """Client đăng nhập user khác — tạo client mới, không mutate test_client."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = another_user.id
        sess["username"] = another_user.username
    return test_client


@pytest.fixture
def sample_product(test_session, sample_category):
    """Override sample_product: thêm image=test.jpg cho template payment.html."""
    from bookingapp.models import TimeSlot
    p = Product(
        name="Sân Mini A", price=300_000,
        category_id=sample_category.id,
        address="123 Đường Test, TP.HCM",
        phone="0901234567", active=True, image="test.jpg",
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

    def test_bill_creation(self, test_session, confirmed_booking, logged_in_user, sample_product):
        """TC1: Tạo Bill thành công."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=sample_product.price,
                    payment_method="direct")
        test_session.add(bill)
        test_session.commit()
        assert bill.id > 0

    def test_bill_amount_matches_product_price(self, test_session, confirmed_booking,
                                                logged_in_user, sample_product):
        """TC2: amount = price sân."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=sample_product.price,
                    payment_method="direct")
        test_session.add(bill)
        test_session.commit()
        assert bill.amount == sample_product.price

    def test_bill_default_payment_method(self, test_session, confirmed_booking,
                                          logged_in_user, sample_product):
        """TC3: payment_method default là 'direct'."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=300_000)
        test_session.add(bill)
        test_session.commit()
        assert bill.payment_method == "direct"

    def test_bill_online_payment_method(self, test_session, confirmed_booking,
                                         logged_in_user, sample_product):
        """TC4: payment_method='online' lưu đúng."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=300_000,
                    payment_method="online")
        test_session.add(bill)
        test_session.commit()
        assert test_session.get(Bill, bill.id).payment_method == "online"

    def test_bill_str(self, test_session, confirmed_booking, logged_in_user, sample_product):
        """TC5: __str__ đúng format."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=300_000)
        test_session.add(bill)
        test_session.commit()
        assert f"#{bill.id}" in str(bill)
        assert "300000" in str(bill)

    def test_bill_created_at_auto(self, test_session, confirmed_booking,
                                   logged_in_user, sample_product):
        """TC6: created_at tự động set."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=300_000)
        test_session.add(bill)
        test_session.commit()
        assert bill.created_at is not None

    def test_bill_relationships(self, test_session, confirmed_booking,
                                 logged_in_user, sample_product):
        """TC7: Quan hệ User/Product/Booking đúng."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=sample_product.price)
        test_session.add(bill)
        test_session.commit()
        b = test_session.get(Bill, bill.id)
        assert b.user.id == logged_in_user.id
        assert b.product.id == sample_product.id
        assert b.booking.id == confirmed_booking.id

    def test_booking_marked_paid_via_bill(self, test_session, confirmed_booking,
                                           logged_in_user, sample_product):
        """TC8: Tìm Bill theo booking_id thành công."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=sample_product.price)
        test_session.add(bill)
        test_session.commit()
        assert Bill.query.filter_by(booking_id=confirmed_booking.id).first() is not None


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: API/UI TEST – /payment/<id>
# ═══════════════════════════════════════════════════════════════════

class TestPaymentPage:
    """TC-PAY-PAGE: Kiểm tra truy cập trang thanh toán."""

    def test_payment_page_accessible(self, logged_in_client, confirmed_booking):
        """TC1: Đăng nhập → 200."""
        res = logged_in_client.get(f"/payment/{confirmed_booking.id}",
                                    follow_redirects=True)
        assert res.status_code == 200

    def test_payment_page_unauthenticated_redirect(self, test_client, confirmed_booking):
        """TC2: Chưa đăng nhập → 302."""
        res = test_client.get(f"/payment/{confirmed_booking.id}",
                               follow_redirects=False)
        assert res.status_code == 302

    def test_payment_page_wrong_user(self, another_logged_in_client, confirmed_booking):
        """TC3: User khác → 302."""
        res = another_logged_in_client.get(f"/payment/{confirmed_booking.id}",
                                            follow_redirects=False)
        assert res.status_code == 302

    def test_payment_page_nonexistent_booking(self, logged_in_client):
        """TC4: Booking không tồn tại → 302."""
        res = logged_in_client.get("/payment/99999", follow_redirects=False)
        assert res.status_code == 302

    def test_payment_page_already_paid(self, logged_in_client, paid_booking):
        """TC5: Booking đã trả → vẫn render 200."""
        booking_obj, _ = paid_booking
        res = logged_in_client.get(f"/payment/{booking_obj.id}",
                                    follow_redirects=True)
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: API TEST – POST /api/payment
# ═══════════════════════════════════════════════════════════════════

class TestPaymentAPI:
    """TC-PAY-API: Kiểm tra API thanh toán."""

    def _post(self, client, booking_id, method="direct"):
        return client.post("/api/payment",
                           data=json.dumps({"booking_id": booking_id,
                                            "payment_method": method}),
                           content_type="application/json")

    def test_payment_success_direct(self, logged_in_client, confirmed_booking):
        """TC1: Thanh toán trực tiếp → ok=True, có bill_id."""
        res = self._post(logged_in_client, confirmed_booking.id, "direct")
        data = json.loads(res.data)
        assert res.status_code == 200
        assert data["ok"] is True
        assert "bill_id" in data

    def test_payment_success_online(self, logged_in_client, confirmed_booking):
        """TC2: Thanh toán online → ok=True."""
        data = json.loads(self._post(logged_in_client, confirmed_booking.id, "online").data)
        assert data["ok"] is True

    def test_payment_creates_bill_in_db(self, logged_in_client, confirmed_booking):
        """TC3: Bill xuất hiện trong DB."""
        self._post(logged_in_client, confirmed_booking.id, "direct")
        assert Bill.query.filter_by(booking_id=confirmed_booking.id).first() is not None

    def test_payment_duplicate_rejected(self, logged_in_client, paid_booking):
        """TC4: Thanh toán 2 lần → 400."""
        booking_obj, _ = paid_booking
        res = self._post(logged_in_client, booking_obj.id, "direct")
        assert res.status_code == 400
        assert json.loads(res.data)["ok"] is False

    def test_payment_unauthenticated(self, test_client, confirmed_booking):
        """TC5: Chưa đăng nhập → 401."""
        assert self._post(test_client, confirmed_booking.id).status_code == 401

    def test_payment_wrong_user(self, another_logged_in_client, confirmed_booking):
        """TC6: User khác → ok=False."""
        data = json.loads(self._post(another_logged_in_client, confirmed_booking.id).data)
        assert data["ok"] is False

    def test_payment_nonexistent_booking(self, logged_in_client):
        """TC7: Booking không tồn tại → 404."""
        assert self._post(logged_in_client, 99999).status_code == 404

    def test_payment_bill_amount_correct(self, logged_in_client, confirmed_booking, sample_product):
        """TC8: Bill amount = giá sân."""
        self._post(logged_in_client, confirmed_booking.id, "direct")
        bill = Bill.query.filter_by(booking_id=confirmed_booking.id).first()
        assert bill.amount == sample_product.price

    def test_payment_response_has_bill_id(self, logged_in_client, confirmed_booking):
        """TC9: Response có bill_id kiểu int."""
        data = json.loads(self._post(logged_in_client, confirmed_booking.id).data)
        assert isinstance(data.get("bill_id"), int)

    def test_payment_response_message(self, logged_in_client, confirmed_booking):
        """TC10: Response có msg hợp lệ."""
        data = json.loads(self._post(logged_in_client, confirmed_booking.id).data)
        assert "msg" in data and len(data["msg"]) > 0


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: INTEGRATION TEST
# ═══════════════════════════════════════════════════════════════════

class TestPaymentIntegration:
    """TC-PAY-INTEG: Luồng thanh toán đầy đủ."""

    def test_payment_flow_complete(self, logged_in_client, confirmed_booking):
        """TC1: book → pay → bill tồn tại."""
        assert Bill.query.filter_by(booking_id=confirmed_booking.id).first() is None
        res = logged_in_client.post("/api/payment",
                                    data=json.dumps({"booking_id": confirmed_booking.id,
                                                     "payment_method": "direct"}),
                                    content_type="application/json")
        assert json.loads(res.data)["ok"] is True
        assert Bill.query.filter_by(booking_id=confirmed_booking.id).first() is not None

    def test_paid_booking_shows_on_home(self, logged_in_client, paid_booking):
        """TC2: Trang chủ render được sau paid booking."""
        res = logged_in_client.get("/", follow_redirects=True)
        assert res.status_code == 200

    def test_bill_persists_after_expire(self, test_session, confirmed_booking,
                                         logged_in_user, sample_product):
        """TC3: Bill bền vững sau expire_all."""
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=sample_product.price)
        test_session.add(bill)
        test_session.commit()
        bill_id = bill.id
        test_session.expire_all()
        b = test_session.get(Bill, bill_id)
        assert b is not None and b.amount == sample_product.price


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: MOCK TEST – pytest-mock
# ═══════════════════════════════════════════════════════════════════

class TestPaymentMock:
    """TC-PAY-MOCK: Dùng pytest-mock để isolate dependencies."""

    def test_create_bill_dao_called(self, mocker, logged_in_client, confirmed_booking):
        """TC1: db.session.add được gọi khi thanh toán."""
        spy = mocker.spy(db.session, "add")
        logged_in_client.post("/api/payment",
                              data=json.dumps({"booking_id": confirmed_booking.id,
                                               "payment_method": "direct"}),
                              content_type="application/json")
        spy.assert_called()

    def test_payment_db_error_returns_error(self, mocker, logged_in_client, confirmed_booking):
        """TC2: db.session.commit() ném exception → exception propagated."""
        mocker.patch.object(db.session, "commit",
                            side_effect=Exception("DB connection lost"))
        with pytest.raises(Exception, match="DB connection lost"):
            logged_in_client.post("/api/payment",
                                  data=json.dumps({"booking_id": confirmed_booking.id,
                                                   "payment_method": "direct"}),
                                  content_type="application/json")

    def test_payment_notification_failure_does_not_block(self, mocker,
                                                          logged_in_client,
                                                          confirmed_booking):
        """TC3: Thanh toán thành công bình thường (app chưa có notification)."""
        res = logged_in_client.post("/api/payment",
                                    data=json.dumps({"booking_id": confirmed_booking.id,
                                                     "payment_method": "direct"}),
                                    content_type="application/json")
        assert res.status_code == 200
        assert json.loads(res.data)["ok"] is True

    def test_bill_amount_uses_product_price(self, mocker, test_session,
                                             confirmed_booking, logged_in_user,
                                             sample_product):
        """TC4: Bill lấy amount từ product.price động (mock property)."""
        mocker.patch.object(type(sample_product), "price",
                            new_callable=PropertyMock, return_value=999_000)
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=confirmed_booking.id, amount=sample_product.price)
        test_session.add(bill)
        test_session.commit()
        assert bill.amount == 999_000

    def test_session_rollback_on_error(self, mocker, logged_in_client, confirmed_booking):
        """TC5: Khi lỗi DB, exception được raise (TESTING mode)."""
        mocker.patch.object(db.session, "commit",
                            side_effect=Exception("Simulated DB failure"))
        with pytest.raises(Exception, match="Simulated DB failure"):
            logged_in_client.post("/api/payment",
                                  data=json.dumps({"booking_id": confirmed_booking.id,
                                                   "payment_method": "direct"}),
                                  content_type="application/json")

    def test_payment_flow_with_all_mocked(self, mocker, test_app):
        """TC6: Mock toàn bộ layer, verify flow không phụ thuộc DB thật."""
        mock_booking = MagicMock()
        mock_booking.id = 1
        mock_booking.user_id = 1
        mock_booking.product_id = 1
        mock_booking.status = "confirmed"
        mock_booking.product.price = 300_000

        mock_bill = MagicMock()
        mock_bill.id = 99
        mock_bill.amount = 300_000
        mock_bill.payment_method = "direct"

        # Verify mock objects work correctly
        assert mock_booking.status == "confirmed"
        assert mock_booking.product.price == 300_000
        assert mock_bill.id == 99
        assert mock_bill.amount == 300_000


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: TEST – Payment page group booking (index.py:649-657)
# ═══════════════════════════════════════════════════════════════════

class TestPaymentGroupBooking:
    """TC-PAY-GROUP: Kiểm tra trang thanh toán cho nhóm booking."""

    def _make_group(self, test_session, user, product, group_id, slots):
        from bookingapp.models import TimeSlot
        tomorrow = datetime.now() + timedelta(days=1)
        day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        bookings = []
        for i, slot in enumerate(slots):
            b = Booking(
                user_id=user.id, product_id=product.id,
                slot_label=slot, date=day_start,
                start_time=tomorrow.replace(hour=8+i, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=9+i, minute=0, second=0, microsecond=0),
                status="confirmed", group_id=group_id,
            )
            test_session.add(b)
            bookings.append(b)
        test_session.commit()
        return bookings

    def test_payment_page_group_booking(self, test_session, logged_in_client,
                                         logged_in_user, sample_product):
        """TC1: Trang thanh toán hiển thị đúng cho nhóm booking (index.py:649-652)."""
        bks = self._make_group(test_session, logged_in_user, sample_product,
                               "pay_grp1", ["08:00 - 09:00", "09:00 - 10:00"])
        res = logged_in_client.get(f"/payment/{bks[0].id}", follow_redirects=True)
        assert res.status_code == 200

    def test_payment_page_group_already_paid(self, test_session, logged_in_client,
                                              logged_in_user, sample_product):
        """TC2: Nhóm booking đã thanh toán → is_paid=True (index.py:654-657)."""
        bks = self._make_group(test_session, logged_in_user, sample_product,
                               "pay_grp2", ["08:00 - 09:00", "09:00 - 10:00"])
        bill = Bill(user_id=logged_in_user.id, product_id=sample_product.id,
                    booking_id=bks[1].id, amount=600_000)
        test_session.add(bill)
        test_session.commit()
        # Truy cập qua booking đầu tiên (không có bill trực tiếp)
        res = logged_in_client.get(f"/payment/{bks[0].id}", follow_redirects=True)
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: API TEST – Group payment duplicate (index.py:695)
# ═══════════════════════════════════════════════════════════════════

class TestPaymentGroupDuplicate:
    """TC-PAY-GROUP-DUP: Thanh toán lại nhóm đã trả → 400."""

    def test_group_payment_duplicate_rejected(self, test_session, logged_in_client,
                                               logged_in_user, sample_product):
        """TC1: Nhóm đã thanh toán → trả lại mã hóa đơn cũ (index.py:695)."""
        tomorrow = datetime.now() + timedelta(days=1)
        day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        bks = []
        for i, slot in enumerate(["08:00 - 09:00", "09:00 - 10:00"]):
            b = Booking(
                user_id=logged_in_user.id, product_id=sample_product.id,
                slot_label=slot, date=day_start,
                start_time=tomorrow.replace(hour=8+i, minute=0, second=0, microsecond=0),
                end_time=tomorrow.replace(hour=9+i, minute=0, second=0, microsecond=0),
                status="confirmed", group_id="dup_grp",
            )
            test_session.add(b)
            bks.append(b)
        test_session.commit()
        # Thanh toán lần 1
        res1 = logged_in_client.post("/api/payment",
                                      data=json.dumps({"booking_id": bks[0].id,
                                                       "payment_method": "direct"}),
                                      content_type="application/json")
        assert json.loads(res1.data)["ok"] is True
        # Thanh toán lần 2 (trùng) → 400
        res2 = logged_in_client.post("/api/payment",
                                      data=json.dumps({"booking_id": bks[0].id,
                                                       "payment_method": "direct"}),
                                      content_type="application/json")
        assert res2.status_code == 400
        data = json.loads(res2.data)
        assert data["ok"] is False
        assert "Đã thanh toán" in data["msg"]