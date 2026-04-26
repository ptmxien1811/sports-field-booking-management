"""
test_base.py – Fixtures dùng chung cho toàn bộ test suite
Dự án: Quản lý đặt sân thể thao
"""

import pytest
from flask import Flask
from bookingapp import db
from bookingapp.models import User, Category, Product, Booking, Bill, Review, TimeSlot, Favorite
from datetime import datetime, timedelta


# ─── Tạo Flask app với SQLite in-memory ──────────────────────────────────────

def create_app():
    """Factory: Flask app dùng SQLite in-memory, không động đến DB thật."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.secret_key = "test_secret_key_for_testing_only"

    db.init_app(app)

    # Đăng ký routes từ index.py
    with app.app_context():
        from bookingapp import index  # noqa: F401 – import để routes được đăng ký

    return app


# ─── Fixtures cốt lõi ────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_app():
    """App fixture: tạo schema trước mỗi test, xóa sau."""
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def test_client(test_app):
    """Flask test client."""
    return test_app.test_client()


@pytest.fixture(scope="function")
def test_session(test_app):
    """SQLAlchemy session, rollback sau mỗi test."""
    with test_app.app_context():
        yield db.session
        db.session.rollback()


# ─── Fixtures dữ liệu dùng chung ─────────────────────────────────────────────

@pytest.fixture
def sample_category(test_session):
    """Category mẫu."""
    c = Category(name="Sân bóng đá")
    test_session.add(c)
    test_session.commit()
    return c


@pytest.fixture
def sample_product(test_session, sample_category):
    """Product mẫu có TimeSlot."""
    p = Product(
        name="Sân Mini A",
        price=300_000,
        category_id=sample_category.id,
        address="123 Đường Test, TP.HCM",
        phone="0901234567",
        active=True,
    )
    test_session.add(p)
    test_session.commit()

    # Thêm một số TimeSlot
    for label in ["08:00 - 09:00", "09:00 - 10:00", "10:00 - 11:00"]:
        ts = TimeSlot(product_id=p.id, label=label, period="morning")
        test_session.add(ts)
    test_session.commit()
    return p


@pytest.fixture
def logged_in_user(test_session):
    """User thường đã được tạo trong DB."""
    u = User(username="testuser", email="test@example.com", phone="0912345678", auth_type="local")
    u.set_password("Test@1234")
    test_session.add(u)
    test_session.commit()
    return u


@pytest.fixture
def admin_user(test_session):
    """User admin."""
    u = User(username="admin", email="admin@example.com", auth_type="local")
    u.set_password("Admin@1234")
    test_session.add(u)
    test_session.commit()
    return u


@pytest.fixture
def logged_in_client(test_client, logged_in_user):
    """Test client đã inject session user thường."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = logged_in_user.id
        sess["username"] = logged_in_user.username
    return test_client


@pytest.fixture
def admin_client(test_client, admin_user):
    """Test client đã inject session admin."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = admin_user.id
        sess["username"] = "admin"
    return test_client


@pytest.fixture
def confirmed_booking(test_session, logged_in_user, sample_product):
    """Booking confirmed trong tương lai (1 ngày sau)."""
    tomorrow = datetime.now() + timedelta(days=1)
    day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    end = start + timedelta(hours=1)

    b = Booking(
        user_id=logged_in_user.id,
        product_id=sample_product.id,
        slot_label="09:00 - 10:00",
        date=day_start,
        start_time=start,
        end_time=end,
        status="confirmed",
    )
    test_session.add(b)
    test_session.commit()
    return b


@pytest.fixture
def paid_booking(test_session, confirmed_booking, logged_in_user, sample_product):
    """Booking đã thanh toán (có Bill kèm theo)."""
    bill = Bill(
        user_id=logged_in_user.id,
        product_id=sample_product.id,
        booking_id=confirmed_booking.id,
        amount=sample_product.price,
        payment_method="direct",
    )
    test_session.add(bill)
    test_session.commit()
    return confirmed_booking, bill