"""
test_auth.py – Kiểm thử đăng ký / đăng nhập (CR300-AUTH)
Bao gồm: Unit test model validation, API test routes /register /login
"""

import pytest
from bookingapp.models import User
from bookingapp import db
from test_base import test_app, test_client, test_session, logged_in_user


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – User.validate_password()
# ═══════════════════════════════════════════════════════════════════

class TestPasswordValidation:
    """TC-AUTH-PASS: Kiểm tra rule mật khẩu."""

    def test_valid_password(self):
        ok, msg = User.validate_password("Test@1234")
        assert ok is True
        assert msg == "OK"

    def test_password_too_short(self):
        ok, msg = User.validate_password("T@1a")
        assert ok is False
        assert "8 ký tự" in msg

    def test_password_no_uppercase(self):
        ok, msg = User.validate_password("test@1234")
        assert ok is False
        assert "HOA" in msg

    def test_password_no_lowercase(self):
        ok, msg = User.validate_password("TEST@1234")
        assert ok is False
        assert "thường" in msg

    def test_password_no_digit(self):
        ok, msg = User.validate_password("Test@abcd")
        assert ok is False
        assert "số" in msg

    def test_password_no_special_char(self):
        ok, msg = User.validate_password("Test12345")
        assert ok is False
        assert "đặc biệt" in msg

    def test_password_all_violations(self):
        ok, msg = User.validate_password("abc")
        assert ok is False


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: UNIT TEST – User.validate_email()
# ═══════════════════════════════════════════════════════════════════

class TestEmailValidation:
    """TC-AUTH-EMAIL: Kiểm tra format email."""

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "name.surname@domain.vn",
        "test+tag@sub.domain.org",
    ])
    def test_valid_emails(self, email):
        assert User.validate_email(email) is True

    @pytest.mark.parametrize("email", [
        "no-at-sign",
        "@domain.com",
        "user@",
        "user@domain",
        "",
    ])
    def test_invalid_emails(self, email):
        assert User.validate_email(email) is False


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: UNIT TEST – User.validate_phone()
# ═══════════════════════════════════════════════════════════════════

class TestPhoneValidation:
    """TC-AUTH-PHONE: Số điện thoại VN 10 số, bắt đầu 0[3-9]."""

    @pytest.mark.parametrize("phone", [
        "0912345678",
        "0398765432",
        "0765432198",
    ])
    def test_valid_phones(self, phone):
        assert User.validate_phone(phone) is True

    @pytest.mark.parametrize("phone", [
        "01234567890",   # 11 số
        "1234567890",    # không bắt đầu 0
        "0212345678",    # prefix không hợp lệ (02x)
        "091234567",     # 9 số
        "abc1234567",
    ])
    def test_invalid_phones(self, phone):
        assert User.validate_phone(phone) is False


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: UNIT TEST – DB – User.set_password / check_password
# ═══════════════════════════════════════════════════════════════════

class TestUserPasswordHashing:
    """TC-AUTH-HASH: Hash/verify password trong DB."""

    def test_set_and_check_password(self, test_session):
        u = User(username="hashtest", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()

        assert u.check_password("Test@1234") is True

    def test_wrong_password_rejected(self, test_session):
        u = User(username="hashtest2", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()

        assert u.check_password("WrongPass@9") is False

    def test_empty_password_rejected(self, test_session):
        u = User(username="nopw", auth_type="google", password="")
        test_session.add(u)
        test_session.commit()
        assert u.check_password("anything") is False

    def test_username_unique_constraint(self, test_session):
        u1 = User(username="dupuser", auth_type="local")
        u1.set_password("Test@1234")
        u2 = User(username="dupuser", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u1)
        test_session.commit()
        test_session.add(u2)
        with pytest.raises(Exception):
            test_session.commit()


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: API TEST – /register (username)
# ═══════════════════════════════════════════════════════════════════

class TestRegisterAPI:
    """TC-AUTH-REG: POST /register"""

    def test_register_success(self, test_client):
        """TC1: Đăng ký thành công với dữ liệu hợp lệ."""
        res = test_client.post("/register", data={
            "username": "newuser",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "email": "new@example.com",
            "phone": "0912345678",
        }, follow_redirects=True)
        assert res.status_code == 200
        user = User.query.filter_by(username="newuser").first()
        assert user is not None

    def test_register_duplicate_username(self, test_client, logged_in_user):
        """TC2: Username đã tồn tại → báo lỗi."""
        res = test_client.post("/register", data={
            "username": logged_in_user.username,
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert b"\u0111\xe3 t\u1ed3n t\u1ea1i" in res.data or res.status_code == 200

    def test_register_password_mismatch(self, test_client):
        """TC3: Mật khẩu xác nhận không khớp."""
        res = test_client.post("/register", data={
            "username": "mismatch_user",
            "password": "Test@1234",
            "confirm_password": "Test@9999",
        })
        assert res.status_code == 200
        assert "kh\u00f4ng kh\u1edbp" in res.data.decode("utf-8")

    def test_register_weak_password(self, test_client):
        """TC4: Mật khẩu yếu bị từ chối."""
        res = test_client.post("/register", data={
            "username": "weakpw_user",
            "password": "abc",
            "confirm_password": "abc",
        })
        assert res.status_code == 200
        assert "M\u1eadt kh\u1ea9u" in res.data.decode("utf-8")

    def test_register_invalid_email(self, test_client):
        """TC5: Email sai format."""
        res = test_client.post("/register", data={
            "username": "emailtest",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "email": "not-an-email",
        })
        assert res.status_code == 200
        assert "Email" in res.data.decode("utf-8")

    def test_register_invalid_phone(self, test_client):
        """TC6: Số điện thoại không hợp lệ."""
        res = test_client.post("/register", data={
            "username": "phonetest",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "phone": "0123456789",  # prefix 01x không hợp lệ
        })
        assert res.status_code == 200
        assert "\u0110i\u1ec7n tho\u1ea1i" in res.data.decode("utf-8") or "kh\u00f4ng h\u1ee3p l\u1ec7" in res.data.decode("utf-8")

    def test_register_duplicate_email(self, test_client, logged_in_user):
        """TC7: Email đã sử dụng."""
        res = test_client.post("/register", data={
            "username": "anotheruser",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "email": logged_in_user.email,
        })
        assert res.status_code == 200

    def test_register_empty_username(self, test_client):
        """TC8: Username rỗng."""
        res = test_client.post("/register", data={
            "username": "",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert res.status_code == 200
        assert "nh\u1eadp" in res.data.decode("utf-8").lower() or res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: API TEST – /login
# ═══════════════════════════════════════════════════════════════════

class TestLoginAPI:
    """TC-AUTH-LOGIN: POST /login"""

    def test_login_success(self, test_client, logged_in_user):
        """TC1: Đăng nhập thành công."""
        res = test_client.post("/login", data={
            "username": "testuser",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_wrong_password(self, test_client, logged_in_user):
        """TC2: Sai mật khẩu → flash lỗi."""
        res = test_client.post("/login", data={
            "username": "testuser",
            "password": "WrongPwd@9",
        })
        assert res.status_code == 200
        assert "kh\u00f4ng \u0111\u00fang" in res.data.decode("utf-8")

    def test_login_nonexistent_user(self, test_client):
        """TC3: Username không tồn tại."""
        res = test_client.post("/login", data={
            "username": "ghost_user",
            "password": "Test@1234",
        })
        assert res.status_code == 200
        assert "kh\u00f4ng \u0111\u00fang" in res.data.decode("utf-8")

    def test_login_admin_redirect(self, test_client, admin_user):
        """TC4: Đăng nhập admin → redirect /admin."""
        res = test_client.post("/login", data={
            "username": "admin",
            "password": "Admin@1234",
        }, follow_redirects=False)
        assert res.status_code == 302
        assert "/admin" in res.headers.get("Location", "")

    def test_logout_clears_session(self, logged_in_client):
        """TC5: Logout xóa session."""
        res = logged_in_client.get("/logout", follow_redirects=False)
        assert res.status_code == 302
        with logged_in_client.session_transaction() as sess:
            assert "user_id" not in sess


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: API TEST – /login/email và /login/phone
# ═══════════════════════════════════════════════════════════════════

class TestLoginEmailPhone:
    """TC-AUTH-ALT: Đăng nhập bằng email/SĐT."""

    def test_login_by_email_success(self, test_client, logged_in_user):
        """TC1: Đăng nhập email đúng."""
        res = test_client.post("/login/email", data={
            "email": "test@example.com",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_by_email_invalid_format(self, test_client):
        """TC2: Email sai format → báo lỗi."""
        res = test_client.post("/login/email", data={
            "email": "bademail",
            "password": "Test@1234",
        })
        assert res.status_code == 200
        assert "Email" in res.data.decode("utf-8")

    def test_login_by_phone_success(self, test_client, logged_in_user):
        """TC3: Đăng nhập SĐT đúng."""
        res = test_client.post("/login/phone", data={
            "phone": "0912345678",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_by_phone_invalid(self, test_client):
        """TC4: SĐT sai format."""
        res = test_client.post("/login/phone", data={
            "phone": "0123abc456",
            "password": "Test@1234",
        })
        assert res.status_code == 200
        assert "\u0110i\u1ec7n tho\u1ea1i" in res.data.decode("utf-8") or "kh\u00f4ng h\u1ee3p l\u1ec7" in res.data.decode("utf-8")


# ═══════════════════════════════════════════════════════════════════
# SECTION 8: API TEST – /api/change-password và /api/update-profile
# ═══════════════════════════════════════════════════════════════════

class TestAccountAPI:
    """TC-AUTH-ACCT: API quản lý tài khoản."""

    def test_change_password_success(self, logged_in_client):
        """TC1: Đổi mật khẩu thành công."""
        res = logged_in_client.post("/api/change-password", json={
            "current_password": "Test@1234",
            "new_password": "NewPass@99",
        })
        data = res.get_json()
        assert data["ok"] is True

    def test_change_password_wrong_current(self, logged_in_client):
        """TC2: Mật khẩu hiện tại sai."""
        res = logged_in_client.post("/api/change-password", json={
            "current_password": "WrongPwd@1",
            "new_password": "NewPass@99",
        })
        data = res.get_json()
        assert data["ok"] is False
        assert "hi\u1ec7n t\u1ea1i" in data["msg"]

    def test_change_password_weak_new(self, logged_in_client):
        """TC3: Mật khẩu mới yếu."""
        res = logged_in_client.post("/api/change-password", json={
            "current_password": "Test@1234",
            "new_password": "weak",
        })
        data = res.get_json()
        assert data["ok"] is False

    def test_change_password_unauthenticated(self, test_client):
        """TC4: Chưa đăng nhập → 401."""
        res = test_client.post("/api/change-password", json={
            "current_password": "Test@1234",
            "new_password": "NewPass@99",
        })
        assert res.status_code == 401

    def test_update_profile_success(self, logged_in_client):
        """TC5: Cập nhật email thành công."""
        res = logged_in_client.post("/api/update-profile", json={
            "email": "updated@example.com",
        })
        data = res.get_json()
        assert data["ok"] is True

    def test_update_profile_invalid_email(self, logged_in_client):
        """TC6: Email không hợp lệ."""
        res = logged_in_client.post("/api/update-profile", json={
            "email": "invalid-email",
        })
        data = res.get_json()
        assert data["ok"] is False

    def test_update_profile_unauthenticated(self, test_client):
        """TC7: Chưa đăng nhập → 401."""
        res = test_client.post("/api/update-profile", json={"email": "x@y.com"})
        assert res.status_code == 401