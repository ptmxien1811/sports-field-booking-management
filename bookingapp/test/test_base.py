# ============================================================
# test_base.py — Nơi chứa các Fixture dùng chung cho toàn bộ Unit Test
# ============================================================

import pytest
import sys
import os

# 1. Thêm đường dẫn gốc của project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 2. Khởi tạo app/db NGAY LẬP TỨC khi module này được load
# Điều này đảm bảo monkey-patch xảy ra TRƯỚC khi bất kỳ test nào chạy
test_app_instance = Flask('bookingapp')
test_app_instance.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
test_app_instance.config['TESTING'] = True
test_app_instance.config['WTF_CSRF_ENABLED'] = False
test_app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
test_app_instance.secret_key = 'test_secret_key_2026'

test_db_instance = SQLAlchemy(test_app_instance)

# 3. Monkey-patch cực mạnh
import bookingapp
bookingapp.app = test_app_instance
bookingapp.db = test_db_instance

# 4. Đăng ký các bảng
from bookingapp import models, admin, index

with test_app_instance.app_context():
    test_db_instance.create_all()


@pytest.fixture(scope='session')
def test_app():
    """Trả về app đã được khởi tạo sẵn"""
    yield test_app_instance


@pytest.fixture(autouse=True)
def clean_db(test_app):
    """Tự động dọn dẹp DB sau mỗi test"""
    yield
    with test_app_instance.app_context():
        test_db_instance.session.rollback()
        for table in reversed(test_db_instance.metadata.sorted_tables):
            test_db_instance.session.execute(table.delete())
        test_db_instance.session.commit()


@pytest.fixture
def test_client(test_app):
    return test_app_instance.test_client()


@pytest.fixture
def test_session(test_app):
    with test_app_instance.app_context():
        yield test_db_instance.session
