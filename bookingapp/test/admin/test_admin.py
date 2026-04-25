# ============================================================
# test_admin.py — Unit Test cho trang Admin (Phần của Long)
# ============================================================

# QUAN TRỌNG: Phải import test_base ĐẦU TIÊN để cấu hình SQLite
import bookingapp.test.test_base as test_base
from bookingapp.test.test_base import test_client, test_session, test_app, clean_db

import pytest
from bookingapp.models import Product, Category, Booking, User, Bill
from bookingapp import db
from datetime import datetime, timedelta


# ============================================================
# PHẦN A: CHUẨN BỊ FIXTURE
# ============================================================

@pytest.fixture
def admin_client(test_client):
    """Client đã đăng nhập bằng tài khoản admin"""
    with test_client.session_transaction() as sess:
        sess["username"] = "admin"
    return test_client


@pytest.fixture
def sample_category(test_session):
    """Tạo một Category mẫu (Sân tennis) trong DB ảo"""
    c = Category(name="Sân tennis")
    test_session.add(c)
    test_session.commit()
    return c


@pytest.fixture
def sample_product(test_session, sample_category):
    """Tạo một Product/Sân mẫu (Sân A1) gắn với category mẫu"""
    p = Product(name="Sân A1", price=300000, category_id=sample_category.id)
    test_session.add(p)
    test_session.commit()
    return p


@pytest.fixture
def seed_admin_data(test_session):
    """Tạo dữ liệu tối thiểu để trang admin dashboard render được"""
    cat = Category(name="Sân bóng đá")
    test_session.add(cat)
    test_session.flush()

    prod = Product(name="Sân Test Dashboard", price=150000, category_id=cat.id)
    test_session.add(prod)
    test_session.flush()

    user = User(username="admin", password="")
    user.set_password("Admin@1234")
    test_session.add(user)
    test_session.flush()

    bill = Bill(user_id=user.id, product_id=prod.id, amount=150000)
    test_session.add(bill)
    test_session.commit()


# ============================================================
# PHẦN B: TEST DASHBOARD ADMIN
# ============================================================

def test_dashboard_accessible(admin_client, seed_admin_data):
    """TC1: Admin truy cập /admin/ thành công"""
    res = admin_client.get("/admin/")
    assert res.status_code == 200


def test_dashboard_no_permission(test_client):
    """TC3: User thường bị redirect khi truy cập /admin/"""
    with test_client.session_transaction() as sess:
        sess["username"] = "regular_user"
    res = test_client.get("/admin/")
    assert res.status_code in [302, 403]


# ============================================================
# PHẦN C: TEST THÊM/XÓA/SỬA SÂN
# ============================================================

def test_delete_product_with_future_booking(test_session, sample_product):
    """TC8: Không được xóa sân nếu có future booking confirmed"""
    u = User(username="user1", password="")
    u.set_password("Test@1234")
    test_session.add(u)
    test_session.commit()

    future = datetime.now() + timedelta(days=3)
    b = Booking(
        user_id=u.id,
        product_id=sample_product.id,
        slot_label="09:00 - 10:00",
        date=future,
        start_time=future,
        end_time=future,
        status="confirmed"
    )
    test_session.add(b)
    test_session.commit()

    future_booking = Booking.query.filter(
        Booking.product_id == sample_product.id,
        Booking.date >= datetime.now(),
        Booking.status == "confirmed"
    ).first()
    assert future_booking is not None


def test_delete_product_past_booking_only(test_session, sample_product):
    """TC9: Xóa sân thành công nếu chỉ có booking quá khứ"""
    future_booking = Booking.query.filter(
        Booking.product_id == sample_product.id,
        Booking.date >= datetime.now(),
        Booking.status == "confirmed"
    ).first()
    assert future_booking is None


def test_product_name_unique(test_session, sample_category):
    """TC5: Tên sân phải duy nhất"""
    p1 = Product(name="Sân Unique", price=100, category_id=sample_category.id)
    test_session.add(p1)
    test_session.commit()

    p2 = Product(name="Sân Unique", price=200, category_id=sample_category.id)
    test_session.add(p2)
    with pytest.raises(Exception):
        test_session.commit()
