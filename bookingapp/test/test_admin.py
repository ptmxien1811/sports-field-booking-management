"""
test_admin.py – Kiểm thử nghiệp vụ Admin
Bao gồm: Unit test dao, API test Flask-Admin routes, UI test Dashboard
"""

import pytest
from flask import Flask
import bookingapp
from bookingapp import db
from bookingapp.models import Product, Category, Booking, User, Bill, Favorite, TimeSlot
from bookingapp.test.test_base import (
    test_client, test_session,
    sample_category, sample_product,
    logged_in_user, admin_user, admin_client,
)
from datetime import datetime, timedelta


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


@pytest.fixture(scope="function")
def test_app():
    """Override test_app: dùng app đã monkey-patch"""
    with _app.app_context():
        db.create_all()
        yield _app
        db.session.remove()
        db.drop_all()


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – dao.get_all_bookings()
# ═══════════════════════════════════════════════════════════════════

from bookingapp.dao import get_all_bookings, get_all_favorites


class TestGetAllBookingsDAO:
    """TC-ADMIN-DAO-BOOK: Kiểm tra hàm get_all_bookings (dành cho Admin)."""

    def test_get_all_bookings_empty(self, test_session):
        """TC1: DB chưa có booking nào → trả về list rỗng."""
        result = get_all_bookings()
        assert result == []

    def test_get_all_bookings_returns_correct_structure(self, test_session):
        """TC2: Có dữ liệu → trả về list dict đúng cấu trúc."""
        cat = Category(name="Sân bóng đá")
        test_session.add(cat)
        test_session.flush()

        prod = Product(name="Sân Admin Test", price=200000, category_id=cat.id)
        test_session.add(prod)
        test_session.flush()

        user = User(username="user_booking", password="")
        user.set_password("Test@1234")
        test_session.add(user)
        test_session.flush()

        tomorrow = datetime.now() + timedelta(days=1)
        booking = Booking(
            user_id=user.id,
            product_id=prod.id,
            slot_label="08:00 - 09:00",
            date=tomorrow,
            start_time=tomorrow.replace(hour=8, minute=0),
            end_time=tomorrow.replace(hour=9, minute=0),
            status="confirmed",
        )
        test_session.add(booking)
        test_session.commit()

        result = get_all_bookings()
        assert len(result) == 1

        item = result[0]
        for key in ["id", "username", "product_name", "category_name",
                     "slot_label", "date", "status"]:
            assert key in item, f"Thiếu key '{key}' trong kết quả"

        assert item["username"] == "user_booking"
        assert item["product_name"] == "Sân Admin Test"
        assert item["category_name"] == "Sân bóng đá"
        assert item["status"] == "confirmed"


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: UNIT TEST – dao.get_all_favorites()
# ═══════════════════════════════════════════════════════════════════

class TestGetAllFavoritesDAO:
    """TC-ADMIN-DAO-FAV: Kiểm tra hàm get_all_favorites (dành cho Admin)."""

    def test_get_all_favorites_empty(self, test_session):
        """TC1: Chưa có ai thả tim → trả về list rỗng."""
        result = get_all_favorites()
        assert result == []

    def test_get_all_favorites_returns_correct_structure(self, test_session):
        """TC2: Có dữ liệu → trả về list dict đúng cấu trúc."""
        cat = Category(name="Sân tennis")
        test_session.add(cat)
        test_session.flush()

        prod = Product(name="Sân Fav Test", price=150000, category_id=cat.id)
        test_session.add(prod)
        test_session.flush()

        user = User(username="user_fav", password="")
        user.set_password("Test@1234")
        test_session.add(user)
        test_session.flush()

        fav = Favorite(user_id=user.id, product_id=prod.id)
        test_session.add(fav)
        test_session.commit()

        result = get_all_favorites()
        assert len(result) == 1

        item = result[0]
        for key in ["id", "username", "product_name", "category_name"]:
            assert key in item, f"Thiếu key '{key}' trong kết quả"

        assert item["username"] == "user_fav"
        assert item["product_name"] == "Sân Fav Test"
        assert item["category_name"] == "Sân tennis"


# ─── Fixtures bổ sung ─────────────────────────────────────────────────────────

@pytest.fixture
def non_admin_client(test_client, logged_in_user):
    """Client đăng nhập user thường (không phải admin)."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = logged_in_user.id
        sess["username"] = logged_in_user.username
    return test_client


@pytest.fixture
def product_with_future_booking(test_session, sample_product, logged_in_user):
    """Sân đang có booking tương lai (confirmed)."""
    future = datetime.now() + timedelta(days=3)
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
    test_session.add(b)
    test_session.commit()
    return sample_product


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: TEST PHÂN QUYỀN (AUTHORIZATION)
# ═══════════════════════════════════════════════════════════════════

ADMIN_SUB_ROUTES = ["/admin/category/", "/admin/product/", "/admin/bill/"]


@pytest.fixture
def seed_dashboard_data(test_session, admin_user, sample_product):
    """Seed dữ liệu tối thiểu để Dashboard /admin/ render được."""
    bill = Bill(user_id=admin_user.id, product_id=sample_product.id,
                amount=100000, payment_method="direct")
    test_session.add(bill)
    test_session.commit()


class TestAdminAuth:
    """TC-ADMIN-AUTH: Kiểm tra phân quyền truy cập Flask-Admin."""

    @pytest.mark.parametrize("url", ["/admin/"] + ADMIN_SUB_ROUTES)
    def test_unauthenticated_redirect(self, test_client, url):
        """Chưa đăng nhập → redirect."""
        res = test_client.get(url, follow_redirects=False)
        assert res.status_code in [302, 403]

    @pytest.mark.parametrize("url", ["/admin/"] + ADMIN_SUB_ROUTES)
    def test_non_admin_redirect(self, non_admin_client, url):
        """User thường → redirect."""
        res = non_admin_client.get(url, follow_redirects=False)
        assert res.status_code in [302, 403]

    @pytest.mark.parametrize("url", ADMIN_SUB_ROUTES)
    def test_admin_sub_routes_accessible(self, admin_client, url):
        """Admin → truy cập sub-routes thành công (200)."""
        res = admin_client.get(url, follow_redirects=True)
        assert res.status_code == 200

    def test_admin_dashboard_accessible(self, admin_client, seed_dashboard_data):
        """Admin → truy cập /admin/ dashboard thành công (200)."""
        res = admin_client.get("/admin/", follow_redirects=True)
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: TEST DB / MODEL LAYER – CATEGORY
# ═══════════════════════════════════════════════════════════════════

class TestAdminCategory:
    """TC-ADMIN-CAT: Kiểm tra CRUD Category qua DB."""

    def test_create_category(self, test_session):
        """TC1: Tạo category thành công."""
        c = Category(name="Sân Tennis")
        test_session.add(c)
        test_session.commit()
        found = Category.query.filter_by(name="Sân Tennis").first()
        assert found is not None
        assert found.id > 0

    def test_category_str(self, test_session):
        """TC2: __str__ trả về tên category."""
        c = Category(name="Cầu Lông")
        test_session.add(c)
        test_session.commit()
        assert str(c) == "Cầu Lông"

    def test_list_categories(self, test_session, sample_category):
        """TC3: Truy vấn danh sách category."""
        cats = Category.query.all()
        assert len(cats) >= 1

    def test_delete_category(self, test_session):
        """TC4: Xóa category không có product → thành công."""
        c = Category(name="Tạm")
        test_session.add(c)
        test_session.commit()
        cid = c.id
        test_session.delete(c)
        test_session.commit()
        assert Category.query.get(cid) is None


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: TEST DB / MODEL LAYER – PRODUCT & LOGIC XÓA SÂN
# ═══════════════════════════════════════════════════════════════════

class TestAdminProduct:
    """TC-ADMIN-PROD: Kiểm tra CRUD Product và logic chặn xóa sân."""

    def test_create_product(self, test_session, sample_category):
        """TC1: Tạo sân thành công."""
        p = Product(name="Sân B1", price=250_000, category_id=sample_category.id, active=True)
        test_session.add(p)
        test_session.commit()
        assert p.id > 0

    def test_product_name_unique(self, test_session, sample_category):
        """TC2: Tên sân phải duy nhất → lỗi khi trùng."""
        p1 = Product(name="Sân Unique Test", price=100, category_id=sample_category.id)
        p2 = Product(name="Sân Unique Test", price=200, category_id=sample_category.id)
        test_session.add(p1)
        test_session.commit()
        test_session.add(p2)
        with pytest.raises(Exception):
            test_session.commit()
        test_session.rollback()

    def test_product_active_default(self, test_session, sample_category):
        """TC3: active mặc định là True."""
        p = Product(name="Sân Default Active", price=100, category_id=sample_category.id)
        test_session.add(p)
        test_session.commit()
        assert p.active is True

    def test_product_deactivate(self, test_session, sample_product):
        """TC4: Tắt active sân."""
        sample_product.active = False
        test_session.commit()
        p = test_session.get(Product, sample_product.id)
        assert p.active is False

    def test_product_str(self, test_session, sample_product):
        """TC5: __str__ trả về tên sân."""
        assert str(sample_product) == sample_product.name

    def test_product_update_price(self, test_session, sample_product):
        """TC6: Cập nhật giá sân."""
        sample_product.price = 500_000
        test_session.commit()
        p = test_session.get(Product, sample_product.id)
        assert p.price == 500_000

    def test_product_only_active_shown(self, test_session, sample_category):
        """TC7: Chỉ sân active=True hiện khi query filter."""
        p_active = Product(name="Active San", price=100, category_id=sample_category.id, active=True)
        p_inactive = Product(name="Inactive San", price=100, category_id=sample_category.id, active=False)
        test_session.add_all([p_active, p_inactive])
        test_session.commit()
        products = Product.query.filter_by(active=True).all()
        names = [p.name for p in products]
        assert "Active San" in names
        assert "Inactive San" not in names

    def test_delete_product_no_future_booking(self, test_session, sample_product):
        """TC8: Xóa sân không có future booking → được phép."""
        future_booking = Booking.query.filter(
            Booking.product_id == sample_product.id,
            Booking.date >= datetime.now(),
            Booking.status == "confirmed"
        ).first()
        assert future_booking is None

    def test_delete_product_blocked_by_future_booking(self, test_session, product_with_future_booking):
        """TC9: Sân có future booking confirmed → chặn xóa."""
        future_booking = Booking.query.filter(
            Booking.product_id == product_with_future_booking.id,
            Booking.date >= datetime.now(),
            Booking.status == "confirmed"
        ).first()
        assert future_booking is not None

    def test_product_cascade_delete_bookings(self, test_session, sample_category):
        """TC10: Xóa sân cascade → xóa cả bookings liên quan."""
        p = Product(name="Cascade San", price=100, category_id=sample_category.id, active=True)
        test_session.add(p)
        test_session.commit()

        u = User(username="cuser", email="c@c.com", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()

        future = datetime.now() + timedelta(days=1)
        b = Booking(
            user_id=u.id, product_id=p.id,
            slot_label="09:00 - 10:00",
            date=future.replace(hour=0, minute=0, second=0, microsecond=0),
            start_time=future.replace(hour=9),
            end_time=future.replace(hour=10),
            status="confirmed",
        )
        test_session.add(b)
        test_session.commit()
        bid = b.id

        test_session.delete(p)
        test_session.commit()
        assert Booking.query.get(bid) is None

    def test_delete_model_success(self, test_session, sample_product):
        """TC11: ProductView.delete_model() xóa sân không có future booking → True."""
        from bookingapp.admin import ProductView
        view = ProductView(Product, db.session)
        pid = sample_product.id
        result = view.delete_model(sample_product)
        assert result is True
        assert Product.query.get(pid) is None

    def test_delete_model_blocked(self, test_session, test_app, product_with_future_booking):
        """TC12: ProductView.delete_model() sân có future booking → False."""
        from bookingapp.admin import ProductView
        view = ProductView(Product, db.session)
        pid = product_with_future_booking.id
        with _app.test_request_context():
            result = view.delete_model(product_with_future_booking)
        assert result is False
        assert Product.query.get(pid) is not None


# ═══════════════════════════════════════════════════════════════════
# FIXTURES BỔ SUNG CHO SECTION 6
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_bill(test_session, sample_product, logged_in_user):
    """Tạo Bill mẫu gắn với user và product."""
    bill = Bill(
        user_id=logged_in_user.id,
        product_id=sample_product.id,
        amount=sample_product.price,
        payment_method="direct",
    )
    test_session.add(bill)
    test_session.commit()
    return bill


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: TEST DB / MODEL LAYER – BILL
# ═══════════════════════════════════════════════════════════════════

class TestAdminBill:
    """TC-ADMIN-BILL: Kiểm tra CRUD Bill qua DB."""

    def test_bill_created(self, test_session, sample_bill):
        """TC1: Bill tồn tại trong DB."""
        b = test_session.get(Bill, sample_bill.id)
        assert b is not None
        assert b.amount == sample_bill.amount

    def test_bill_str(self, test_session, sample_bill):
        """TC2: __str__ bill đúng format."""
        assert f"#{sample_bill.id}" in str(sample_bill)

    def test_admin_delete_bill(self, test_session, sample_bill):
        """TC3: Admin xóa bill thành công."""
        bid = sample_bill.id
        test_session.delete(sample_bill)
        test_session.commit()
        assert Bill.query.get(bid) is None

    def test_bill_count(self, test_session, sample_bill):
        """TC4: Đếm tổng bill chính xác."""
        from sqlalchemy import func
        count = test_session.query(func.count(Bill.id)).scalar()
        assert count >= 1

    def test_total_revenue(self, test_session, sample_bill):
        """TC5: Tổng doanh thu tính đúng."""
        from sqlalchemy import func
        total = test_session.query(func.sum(Bill.amount)).scalar()
        assert total >= sample_bill.amount

    def test_bill_payment_method_stored(self, test_session, sample_bill):
        """TC6: payment_method được lưu đúng."""
        b = test_session.get(Bill, sample_bill.id)
        assert b.payment_method in ["direct", "online"]

    def test_bill_list_admin_api(self, admin_client, sample_bill):
        """TC7: Admin truy cập trang quản lý bill thành công."""
        res = admin_client.get("/admin/bill/", follow_redirects=True)
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: UNIT TEST – TimeSlotInlineModel (auto-period)
# ═══════════════════════════════════════════════════════════════════

class TestTimeSlotPeriod:
    """TC-ADMIN-SLOT: Kiểm tra logic tự động gán ca (Sáng/Chiều/Tối)."""

    def test_morning_period(self, test_session, sample_product):
        """TC1: Giờ 06-11 → period = morning."""
        ts = TimeSlot(product_id=sample_product.id, label="08:00 - 09:00", period="morning")
        test_session.add(ts)
        test_session.commit()
        hour = int(ts.label.split(":")[0])
        assert 6 <= hour < 12
        assert ts.period == "morning"

    def test_afternoon_period(self, test_session, sample_product):
        """TC2: Giờ 13-18 → period = afternoon."""
        ts = TimeSlot(product_id=sample_product.id, label="14:00 - 15:00", period="afternoon")
        test_session.add(ts)
        test_session.commit()
        hour = int(ts.label.split(":")[0])
        assert 13 <= hour < 19
        assert ts.period == "afternoon"

    def test_evening_period(self, test_session, sample_product):
        """TC3: Giờ 19-21 → period = evening."""
        ts = TimeSlot(product_id=sample_product.id, label="20:00 - 21:00", period="evening")
        test_session.add(ts)
        test_session.commit()
        hour = int(ts.label.split(":")[0])
        assert hour >= 19
        assert ts.period == "evening"

    def test_timeslot_str(self, test_session, sample_product):
        """TC4: __str__ trả về label."""
        ts = TimeSlot(product_id=sample_product.id, label="09:00 - 10:00", period="morning")
        test_session.add(ts)
        test_session.commit()
        assert str(ts) == "09:00 - 10:00"

    def test_on_model_change_morning(self, test_session, sample_product):
        """TC5: on_model_change gán period=morning cho giờ sáng."""
        from bookingapp.admin import TimeSlotInlineModel
        ts = TimeSlot(product_id=sample_product.id, label="08:00 - 09:00")
        inline = TimeSlotInlineModel(TimeSlot)
        inline.on_model_change(form=None, model=ts, is_created=True)
        assert ts.period == "morning"

    def test_on_model_change_afternoon(self, test_session, sample_product):
        """TC6: on_model_change gán period=afternoon cho giờ chiều."""
        from bookingapp.admin import TimeSlotInlineModel
        ts = TimeSlot(product_id=sample_product.id, label="15:00 - 16:00")
        inline = TimeSlotInlineModel(TimeSlot)
        inline.on_model_change(form=None, model=ts, is_created=True)
        assert ts.period == "afternoon"

    def test_on_model_change_evening(self, test_session, sample_product):
        """TC7: on_model_change gán period=evening cho giờ tối."""
        from bookingapp.admin import TimeSlotInlineModel
        ts = TimeSlot(product_id=sample_product.id, label="20:00 - 21:00")
        inline = TimeSlotInlineModel(TimeSlot)
        inline.on_model_change(form=None, model=ts, is_created=True)
        assert ts.period == "evening"


# ═══════════════════════════════════════════════════════════════════
# SECTION 8: TEST ADMIN DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════════

class TestAdminDashboardStats:
    """TC-ADMIN-STATS: Kiểm tra số liệu thống kê trên Dashboard."""

    def test_stats_totals(self, test_session, logged_in_user, sample_category,
                          sample_product, sample_bill):
        """TC1: Dashboard thống kê đúng số user, sân, category, bill."""
        user_count = User.query.count()
        cat_count = Category.query.count()
        prod_count = Product.query.count()
        bill_count = Bill.query.count()

        assert user_count >= 1
        assert cat_count >= 1
        assert prod_count >= 1
        assert bill_count >= 1

    def test_dashboard_renders_stats(self, admin_client, seed_dashboard_data):
        """TC2: Admin truy cập /admin/ → trang hiển thị số liệu thống kê."""
        res = admin_client.get("/admin/", follow_redirects=True)
        assert res.status_code == 200
        html = res.data.decode("utf-8")
        assert "100" in html  # seed_dashboard_data tạo bill 100000

    def test_dashboard_no_date_filter(self, admin_client, seed_dashboard_data):
        """TC3: /stats không có filter → trả về tất cả."""
        res = admin_client.get("/stats", follow_redirects=True)
        assert res.status_code == 200
