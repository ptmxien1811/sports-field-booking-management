"""
conftest.py – Fixtures dùng chung cho toàn bộ Integration tests.
"""

import pytest
from datetime import datetime, timedelta

from bookingapp import db
from bookingapp.models import User, Category, Product, Booking, Bill, TimeSlot

from bookingapp.test.test_base import (
    create_app,
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, admin_user,
    logged_in_client, admin_client,
    confirmed_booking, paid_booking,
)


@pytest.fixture
def second_user(test_session):
    """User thứ hai dùng để kiểm tra cô lập dữ liệu."""
    u = User(username="integ_user2", email="integ2@test.com",
             phone="0911222333", auth_type="local")
    u.set_password("Integ@1234")
    test_session.add(u)
    test_session.commit()
    return u


@pytest.fixture
def second_client(test_client, second_user):
    """Test client đã đăng nhập với second_user."""
    with test_client.session_transaction() as sess:
        sess["user_id"] = second_user.id
        sess["username"] = second_user.username
    return test_client


@pytest.fixture
def product_with_slots(test_session, sample_category):
    """Sân có đầy đủ slots để test đặt nhiều giờ."""
    p = Product(
        name="Sân Tích Hợp A",
        price=200_000,
        category_id=sample_category.id,
        address="99 Đường Tích Hợp, TP.HCM",
        phone="0909090909",
        active=True,
        image="test.jpg",
    )
    test_session.add(p)
    test_session.commit()
    for label, period in [
        ("08:00 - 09:00", "morning"),
        ("09:00 - 10:00", "morning"),
        ("10:00 - 11:00", "morning"),
        ("14:00 - 15:00", "afternoon"),
        ("15:00 - 16:00", "afternoon"),
    ]:
        test_session.add(TimeSlot(product_id=p.id, label=label, period=period))
    test_session.commit()
    return p


@pytest.fixture
def future_date():
    return (datetime.now() + timedelta(days=3)).date()