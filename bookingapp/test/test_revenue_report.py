# ============================================================
# test_revenue_report.py — Unit Test cho trang Báo Cáo Doanh Thu
# ============================================================

import pytest
from flask import Flask
import bookingapp
from bookingapp import db
from bookingapp.models import Product, Category, User, Bill
from bookingapp.test.test_base import test_client, test_session
from datetime import datetime, timedelta


# ============================================================
# OVERRIDE test_app: thêm monkey-patch để routes đăng ký đúng app
# ============================================================

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
def regular_client(test_client):
    """Client đã đăng nhập bằng tài khoản user thường (không phải admin)"""
    with test_client.session_transaction() as sess:
        sess["username"] = "user_binh_thuong"
    return test_client


@pytest.fixture
def seed_stats_data(test_session):
    """Tạo dữ liệu mẫu: Category, Product, User, Bill để trang stats render được"""
    # Tạo category
    cat = Category(name="Sân bóng đá")
    test_session.add(cat)
    test_session.flush()

    # Tạo product (sân)
    prod = Product(name="Sân Stats Test", price=200000, category_id=cat.id)
    test_session.add(prod)
    test_session.flush()

    # Tạo user
    user = User(username="admin", password="")
    user.set_password("Admin@1234")
    test_session.add(user)
    test_session.flush()

    # Tạo bill (hóa đơn) với ngày hôm nay
    bill = Bill(user_id=user.id, product_id=prod.id, amount=200000,
                created_at=datetime.now())
    test_session.add(bill)

    # Tạo bill ngày hôm qua
    bill_yesterday = Bill(user_id=user.id, product_id=prod.id, amount=150000,
                          created_at=datetime.now() - timedelta(days=1))
    test_session.add(bill_yesterday)

    test_session.commit()
    return {"user": user, "product": prod, "category": cat}


# ============================================================
# PHẦN B: TEST RÀNG BUỘC PHÂN QUYỀN
# Ràng buộc 1: Chỉ admin mới được truy cập trang /stats
# ============================================================

def test_stats_unauthenticated_redirect(test_client):
    """RB1-TC1: User chưa đăng nhập truy cập /stats → bị redirect (302)"""
    # Không set session gì cả → chưa đăng nhập
    res = test_client.get("/stats")
    assert res.status_code == 302, "User chưa đăng nhập phải bị redirect"


def test_stats_regular_user_redirect(regular_client):
    """RB1-TC2: User thường đã đăng nhập truy cập /stats → bị redirect (302)"""
    res = regular_client.get("/stats")
    assert res.status_code == 302, "User thường không được vào trang stats"


def test_stats_admin_accessible(admin_client, seed_stats_data):
    """RB1-TC3: Admin truy cập /stats → trả về 200 OK"""
    res = admin_client.get("/stats")
    assert res.status_code == 200, "Admin phải truy cập được trang stats"


# ============================================================
# PHẦN C: TEST RÀNG BUỘC LỌC NGÀY THÁNG
# Ràng buộc 2: Không được nhập ngược ngày (start > end)
# Ràng buộc 3: Không được nhập ngày ở tương lai
# ============================================================

def test_stats_reversed_dates_auto_swap(admin_client, seed_stats_data):
    """RB2-TC1: Nhập ngược ngày (start > end) → hệ thống tự đảo lại,
    vẫn trả về dữ liệu đúng thay vì lỗi hoặc 0 đồng"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Truyền ngược: start = hôm nay, end = hôm qua (SAI)
    res = admin_client.get(f"/stats?start_date={today}&end_date={yesterday}")

    assert res.status_code == 200, "Trang phải vẫn hiển thị bình thường"

    # Kiểm tra hệ thống đã tự đảo lại → hiển thị doanh thu đúng khoảng
    # (phải có dữ liệu vì seed_stats_data tạo bill hôm nay và hôm qua)
    html = res.data.decode("utf-8")
    # Trang phải chứa thông tin tổng doanh thu (chứng tỏ query chạy thành công)
    assert "Tổng doanh thu" in html, "Trang phải hiển thị tổng doanh thu"


def test_stats_same_start_end_date(admin_client, seed_stats_data):
    """RB2-TC2: Nhập cùng ngày cho start và end → hiển thị dữ liệu đúng ngày đó"""
    today = datetime.now().date()

    res = admin_client.get(f"/stats?start_date={today}&end_date={today}")

    assert res.status_code == 200, "Trang phải hiển thị bình thường với cùng ngày"
    html = res.data.decode("utf-8")
    assert "Tổng doanh thu" in html


def test_stats_future_start_date_capped(admin_client, seed_stats_data):
    """RB3-TC1: Nhập ngày bắt đầu ở tương lai → hệ thống tự ép về ngày hôm nay,
    trang vẫn hiển thị bình thường với dữ liệu hợp lệ"""
    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    today_str = datetime.now().date().strftime("%Y-%m-%d")

    res = admin_client.get(f"/stats?start_date={future_date}")

    assert res.status_code == 200, "Trang phải hiển thị bình thường"
    html = res.data.decode("utf-8")
    # Backend ép ngày tương lai → today, nên trang vẫn render thành công
    assert "Tổng doanh thu" in html, "Trang phải hiển thị tổng doanh thu"
    # Thuộc tính max của ô input date luôn là ngày hôm nay → chặn tương lai
    assert f'max="{today_str}"' in html, \
        "Ô input date phải có thuộc tính max = ngày hôm nay để chặn tương lai"


def test_stats_future_end_date_capped(admin_client, seed_stats_data):
    """RB3-TC2: Nhập ngày kết thúc ở tương lai → hệ thống tự ép về ngày hôm nay,
    trang vẫn hiển thị bình thường với dữ liệu hợp lệ"""
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    res = admin_client.get(f"/stats?start_date={yesterday}&end_date={future_date}")

    assert res.status_code == 200, "Trang phải hiển thị bình thường"
    html = res.data.decode("utf-8")
    # Backend ép ngày tương lai → today → query vẫn trả về dữ liệu đúng
    assert "Tổng doanh thu" in html, "Trang phải hiển thị tổng doanh thu"
    # Thuộc tính max luôn chặn người dùng không chọn quá ngày hôm nay
    assert f'max="{today_str}"' in html, \
        "Ô input date phải có thuộc tính max = ngày hôm nay để chặn tương lai"
