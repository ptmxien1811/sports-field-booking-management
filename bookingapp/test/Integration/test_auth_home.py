"""
test_integ_auth_home.py – INTEG-01: Auth → Home
Kiểm tra luồng đăng ký / đăng nhập ↔ hiển thị trang chủ.
"""

import pytest
from bookingapp.models import User


class TestAuthToHome:
    """INTEG-01: Kiểm tra luồng Auth ↔ Home page."""

    def test_register_then_access_home(self, test_client):
        """
        TC1: Đăng ký tài khoản mới → session được set → trang chủ hiển thị username.
        Kiểm tra: register route → session → home render.
        """
        res = test_client.post("/register", data={
            "username": "integ_register",
            "password": "Integ@1234",
            "confirm_password": "Integ@1234",
            "email": "integ@reg.com",
            "phone": "0934567890",
        }, follow_redirects=True)

        assert res.status_code == 200
        assert "integ_register".encode() in res.data

        u = User.query.filter_by(username="integ_register").first()
        assert u is not None
        assert u.auth_type == "local"

    def test_login_then_home_shows_username(self, test_client, logged_in_user):
        """
        TC2: Đăng nhập thành công → session chứa user_id, username.
        Home render có username của user.
        """
        res = test_client.post("/login", data={
            "username": "testuser",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"testuser" in res.data

    def test_login_sets_session_correctly(self, test_client, logged_in_user):
        """
        TC3: Sau login, session chứa đúng user_id và username.
        Kiểm tra tích hợp: route login → session management.
        """
        test_client.post("/login", data={
            "username": "testuser",
            "password": "Test@1234",
        })
        with test_client.session_transaction() as sess:
            assert sess.get("user_id") == logged_in_user.id
            assert sess.get("username") == "testuser"

    def test_logout_clears_session_and_home_is_guest(self, logged_in_client, logged_in_user):
        """
        TC4: Logout → session xóa → trang chủ không còn username.
        Tích hợp: logout route → session clear → home route.
        """
        res = logged_in_client.get("/logout", follow_redirects=True)
        assert res.status_code == 200

        with logged_in_client.session_transaction() as sess:
            assert "user_id" not in sess
            assert "username" not in sess

    def test_duplicate_register_rejected_and_old_user_intact(self, test_client, logged_in_user):
        """
        TC5: Đăng ký username đã tồn tại → từ chối, user cũ không bị ảnh hưởng.
        """
        res = test_client.post("/register", data={
            "username": "testuser",
            "password": "Integ@1234",
            "confirm_password": "Integ@1234",
        })
        assert res.status_code == 200
        assert "tồn tại".encode("utf-8") in res.data

        u = User.query.filter_by(username="testuser").first()
        assert u is not None
        assert u.check_password("Test@1234")

    def test_admin_login_redirects_to_admin_panel(self, test_client, admin_user):
        """
        TC6: Đăng nhập admin → redirect về /admin (không phải /home).
        Tích hợp: login route → role check → admin redirect.
        """
        res = test_client.post("/login", data={
            "username": "admin",
            "password": "Admin@1234",
        }, follow_redirects=False)
        assert res.status_code == 302
        assert "/admin" in res.headers.get("Location", "")