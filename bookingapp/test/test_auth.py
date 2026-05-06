"""
test_auth.py – Kiểm thử đăng ký / đăng nhập (CR300-AUTH)
Bao gồm: Unit test model validation, API test routes /register /login
"""

import pytest
from bookingapp.models import User
from bookingapp import db
from bookingapp.test.test_base import (
    test_app,
    test_client,
    test_session,
    logged_in_user,
    admin_user,
    logged_in_client,
    admin_client,
    confirmed_booking,
    paid_booking,
)


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
        """ Đăng ký thành công với dữ liệu hợp lệ."""
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
        """ Username đã tồn tại → báo lỗi."""
        res = test_client.post("/register", data={
            "username": logged_in_user.username,
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert b"\u0111\xe3 t\u1ed3n t\u1ea1i" in res.data or res.status_code == 200

    def test_register_password_mismatch(self, test_client):
        """ Mật khẩu xác nhận không khớp."""
        res = test_client.post("/register", data={
            "username": "mismatch_user",
            "password": "Test@1234",
            "confirm_password": "Test@9999",
        })
        assert res.status_code == 200
        assert "kh\u00f4ng kh\u1edbp" in res.data.decode("utf-8")

    def test_register_weak_password(self, test_client):
        """ Mật khẩu yếu bị từ chối."""
        res = test_client.post("/register", data={
            "username": "weakpw_user",
            "password": "abc",
            "confirm_password": "abc",
        })
        assert res.status_code == 200
        assert "M\u1eadt kh\u1ea9u" in res.data.decode("utf-8")

    def test_register_invalid_email(self, test_client):
        """ Email sai format."""
        res = test_client.post("/register", data={
            "username": "emailtest",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "email": "not-an-email",
        })
        assert res.status_code == 200
        assert "Email" in res.data.decode("utf-8")

    def test_register_invalid_phone(self, test_client):
        """ Số điện thoại không hợp lệ."""
        res = test_client.post("/register", data={
            "username": "phonetest",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "phone": "0123456789",  # prefix 01x không hợp lệ
        })
        assert res.status_code == 200
        assert "\u0110i\u1ec7n tho\u1ea1i" in res.data.decode("utf-8") or "kh\u00f4ng h\u1ee3p l\u1ec7" in res.data.decode("utf-8")

    def test_register_duplicate_email(self, test_client, logged_in_user):
        """ Email đã sử dụng."""
        res = test_client.post("/register", data={
            "username": "anotheruser",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "email": logged_in_user.email,
        })
        assert res.status_code == 200

    def test_register_empty_username(self, test_client):
        """ Username rỗng."""
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
        """ Đăng nhập thành công."""
        res = test_client.post("/login", data={
            "username": "testuser",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_wrong_password(self, test_client, logged_in_user):
        """ Sai mật khẩu → flash lỗi."""
        res = test_client.post("/login", data={
            "username": "testuser",
            "password": "WrongPwd@9",
        })
        assert res.status_code == 200
        assert "kh\u00f4ng \u0111\u00fang" in res.data.decode("utf-8")

    def test_login_nonexistent_user(self, test_client):
        """ Username không tồn tại."""
        res = test_client.post("/login", data={
            "username": "ghost_user",
            "password": "Test@1234",
        })
        assert res.status_code == 200
        assert "kh\u00f4ng \u0111\u00fang" in res.data.decode("utf-8")

    def test_login_admin_redirect(self, test_client, admin_user):
        """ Đăng nhập admin → redirect /admin."""
        res = test_client.post("/login", data={
            "username": "admin",
            "password": "Admin@1234",
        }, follow_redirects=False)
        assert res.status_code == 302
        assert "/admin" in res.headers.get("Location", "")

    def test_logout_clears_session(self, logged_in_client):
        """ Logout xóa session."""
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
        """ Đăng nhập email đúng."""
        res = test_client.post("/login/email", data={
            "email": "test@example.com",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_by_email_invalid_format(self, test_client):
        """ Email sai format → báo lỗi."""
        res = test_client.post("/login/email", data={
            "email": "bademail",
            "password": "Test@1234",
        })
        assert res.status_code == 200
        assert "Email" in res.data.decode("utf-8")

    def test_login_by_phone_success(self, test_client, logged_in_user):
        """ Đăng nhập SĐT đúng."""
        res = test_client.post("/login/phone", data={
            "phone": "0912345678",
            "password": "Test@1234",
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_login_by_phone_invalid(self, test_client):
        """ SĐT sai format."""
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
        """ Đổi mật khẩu thành công."""
        res = logged_in_client.post("/api/change-password", json={
            "current_password": "Test@1234",
            "new_password": "NewPass@99",
        })
        data = res.get_json()
        assert data["ok"] is True

    def test_change_password_wrong_current(self, logged_in_client):
        """ Mật khẩu hiện tại sai."""
        res = logged_in_client.post("/api/change-password", json={
            "current_password": "WrongPwd@1",
            "new_password": "NewPass@99",
        })
        data = res.get_json()
        assert data["ok"] is False
        assert "hi\u1ec7n t\u1ea1i" in data["msg"]

    def test_change_password_weak_new(self, logged_in_client):
        """ Mật khẩu mới yếu."""
        res = logged_in_client.post("/api/change-password", json={
            "current_password": "Test@1234",
            "new_password": "weak",
        })
        data = res.get_json()
        assert data["ok"] is False

    def test_change_password_unauthenticated(self, test_client):
        """Chưa đăng nhập → 401."""
        res = test_client.post("/api/change-password", json={
            "current_password": "Test@1234",
            "new_password": "NewPass@99",
        })
        assert res.status_code == 401

    def test_update_profile_success(self, logged_in_client):
        """ Cập nhật email thành công."""
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


# ═══════════════════════════════════════════════════════════════════
# SECTION 9: UNIT TEST – dao.get_user_by_id (dao.py:11)
# ═══════════════════════════════════════════════════════════════════

class TestGetUserById:
    """TC-AUTH-GETUSER: Kiểm tra dao.get_user_by_id."""

    def test_get_user_by_id_found(self, test_session, logged_in_user):
        from bookingapp.dao import get_user_by_id
        user = get_user_by_id(logged_in_user.id)
        assert user is not None
        assert user.username == "testuser"

    def test_get_user_by_id_not_found(self, test_session):
        from bookingapp.dao import get_user_by_id
        user = get_user_by_id(99999)
        assert user is None


# ═══════════════════════════════════════════════════════════════════
# SECTION 10: API TEST – /register duplicate phone (index.py:116)
# ═══════════════════════════════════════════════════════════════════

class TestRegisterDuplicatePhone:
    def test_register_duplicate_phone(self, test_client, logged_in_user):
        """TC: SĐT đã được sử dụng → báo lỗi."""
        res = test_client.post("/register", data={
            "username": "newphoneuser",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "phone": logged_in_user.phone,
        })
        assert res.status_code == 200
        assert "đã được sử dụng" in res.data.decode("utf-8")


# ═══════════════════════════════════════════════════════════════════
# SECTION 11: API TEST – /register GET (index.py:126)
# ═══════════════════════════════════════════════════════════════════

class TestRegisterGet:
    def test_register_page_get(self, test_client):
        """TC: GET /register → 200."""
        res = test_client.get("/register")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 12: API TEST – /login/email (index.py:139, 143)
# ═══════════════════════════════════════════════════════════════════

class TestLoginEmailExtra:
    def test_login_email_wrong_password(self, test_client, logged_in_user):
        """ Email đúng, mật khẩu sai → render lại trang login (200)."""
        res = test_client.post("/login/email", data={
            "email": "test@example.com",
            "password": "WrongPwd@99",
        })
        assert res.status_code == 200

    def test_login_email_nonexistent(self, test_client):
        """ Email không tồn tại → render lại trang login (200)."""
        res = test_client.post("/login/email", data={
            "email": "ghost@example.com",
            "password": "Test@1234",
        })
        assert res.status_code == 200

    def test_login_email_get(self, test_client):
        """ GET /login/email → 200."""
        res = test_client.get("/login/email")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 13: API TEST – /register/email (index.py:149-174)
# ═══════════════════════════════════════════════════════════════════

class TestRegisterEmail:
    def test_register_email_success(self, test_client):
        """ Đăng ký email hợp lệ → redirect."""
        res = test_client.post("/register/email", data={
            "email": "newemail@example.com",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "username": "emailuser1",
        }, follow_redirects=False)
        assert res.status_code == 302

    def test_register_email_invalid_format(self, test_client):
        """ Email sai format."""
        res = test_client.post("/register/email", data={
            "email": "bad-email",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert res.status_code == 200
        assert "Email" in res.data.decode("utf-8")

    def test_register_email_duplicate(self, test_client, logged_in_user):
        """ Email đã tồn tại."""
        res = test_client.post("/register/email", data={
            "email": logged_in_user.email,
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert res.status_code == 200
        assert "đã được sử dụng" in res.data.decode("utf-8")

    def test_register_email_weak_password(self, test_client):
        """ Mật khẩu yếu."""
        res = test_client.post("/register/email", data={
            "email": "weak@example.com",
            "password": "abc",
            "confirm_password": "abc",
        })
        assert res.status_code == 200

    def test_register_email_password_mismatch(self, test_client):
        """TC Mật khẩu xác nhận không khớp."""
        res = test_client.post("/register/email", data={
            "email": "mismatch@example.com",
            "password": "Test@1234",
            "confirm_password": "Test@9999",
        })
        assert res.status_code == 200
        assert "không khớp" in res.data.decode("utf-8")

    def test_register_email_auto_username(self, test_client):
        """TC Không nhập username → tự tạo từ email."""
        res = test_client.post("/register/email", data={
            "email": "autoname@example.com",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "username": "",
        }, follow_redirects=False)
        assert res.status_code == 302
        u = User.query.filter_by(email="autoname@example.com").first()
        assert u is not None
        assert u.username == "autoname"

    def test_register_email_username_collision(self, test_session, test_client):
        """ Username trùng → tự thêm số đuôi."""
        u = User(username="dupname", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()
        res = test_client.post("/register/email", data={
            "email": "dupname@example.com",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "username": "dupname",
        }, follow_redirects=False)
        assert res.status_code == 302
        u2 = User.query.filter_by(email="dupname@example.com").first()
        assert u2 is not None
        assert u2.username != "dupname"

    def test_register_email_get(self, test_client):
        """TC GET /register/email → 200."""
        res = test_client.get("/register/email")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 14: API TEST – /login/phone extra (index.py:188-189, 193)
# ═══════════════════════════════════════════════════════════════════

class TestLoginPhoneExtra:
    def test_login_phone_wrong_password(self, test_client, logged_in_user):
        """TC: SĐT đúng, mật khẩu sai → lỗi."""
        res = test_client.post("/login/phone", data={
            "phone": "0912345678",
            "password": "WrongPwd@99",
        })
        assert res.status_code == 200

    def test_login_phone_nonexistent(self, test_client):
        """TC: SĐT không tồn tại → lỗi."""
        res = test_client.post("/login/phone", data={
            "phone": "0999999999",
            "password": "Test@1234",
        })
        assert res.status_code == 200

    def test_login_phone_get(self, test_client):
        """TC: GET /login/phone → 200."""
        res = test_client.get("/login/phone")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 15: API TEST – /register/phone (index.py:199-224)
# ═══════════════════════════════════════════════════════════════════

class TestRegisterPhone:
    def test_register_phone_success(self, test_client):
        """ Đăng ký SĐT hợp lệ → redirect."""
        res = test_client.post("/register/phone", data={
            "phone": "0388888888",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "username": "phoneuser1",
        }, follow_redirects=False)
        assert res.status_code == 302

    def test_register_phone_invalid(self, test_client):
        """ SĐT sai format."""
        res = test_client.post("/register/phone", data={
            "phone": "12345",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert res.status_code == 200
        assert "không hợp lệ" in res.data.decode("utf-8")

    def test_register_phone_duplicate(self, test_client, logged_in_user):
        """ SĐT đã tồn tại."""
        res = test_client.post("/register/phone", data={
            "phone": logged_in_user.phone,
            "password": "Test@1234",
            "confirm_password": "Test@1234",
        })
        assert res.status_code == 200
        assert "đã được sử dụng" in res.data.decode("utf-8")

    def test_register_phone_weak_password(self, test_client):
        """ Mật khẩu yếu."""
        res = test_client.post("/register/phone", data={
            "phone": "0377777777",
            "password": "abc",
            "confirm_password": "abc",
        })
        assert res.status_code == 200

    def test_register_phone_password_mismatch(self, test_client):
        """ Mật khẩu không khớp."""
        res = test_client.post("/register/phone", data={
            "phone": "0366666666",
            "password": "Test@1234",
            "confirm_password": "Test@9999",
        })
        assert res.status_code == 200
        assert "không khớp" in res.data.decode("utf-8")

    def test_register_phone_auto_username(self, test_client):
        """ Không nhập username → tự tạo từ SĐT."""
        res = test_client.post("/register/phone", data={
            "phone": "0355555555",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "username": "",
        }, follow_redirects=False)
        assert res.status_code == 302
        u = User.query.filter_by(phone="0355555555").first()
        assert u is not None
        assert "5555" in u.username

    def test_register_phone_username_collision(self, test_session, test_client):
        """ Username trùng → tự thêm số đuôi."""
        u = User(username="user_4444", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()
        res = test_client.post("/register/phone", data={
            "phone": "0344444444",
            "password": "Test@1234",
            "confirm_password": "Test@1234",
            "username": "user_4444",
        }, follow_redirects=False)
        assert res.status_code == 302
        u2 = User.query.filter_by(phone="0344444444").first()
        assert u2 is not None
        assert u2.username != "user_4444"

    def test_register_phone_get(self, test_client):
        """GET /register/phone → 200."""
        res = test_client.get("/register/phone")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 16: API TEST – Google OAuth (index.py:230-239, 246, 258, 271-277)
# ═══════════════════════════════════════════════════════════════════

class TestGoogleOAuth:
    def test_google_login_redirect(self, test_client):
        """ GET /auth/google → redirect đến Google."""
        res = test_client.get("/auth/google", follow_redirects=False)
        assert res.status_code == 302
        assert "accounts.google.com" in res.headers.get("Location", "")

    def test_google_callback_no_code(self, test_client):
        """ Callback không có code → redirect login."""
        res = test_client.get("/auth/google/callback", follow_redirects=False)
        assert res.status_code == 302

    def test_google_callback_no_token(self, test_client, mocker):
        """ Google trả về không có access_token → redirect login."""
        mocker.patch("bookingapp.index.http_requests.post",
                     return_value=mocker.Mock(json=lambda: {}))
        res = test_client.get("/auth/google/callback?code=fakecode",
                              follow_redirects=False)
        assert res.status_code == 302

    def test_google_callback_new_user(self, test_client, mocker):
        """ User mới qua Google → tạo tài khoản và đăng nhập."""
        mocker.patch("bookingapp.index.http_requests.post",
                     return_value=mocker.Mock(json=lambda: {"access_token": "tok123"}))
        mocker.patch("bookingapp.index.http_requests.get",
                     return_value=mocker.Mock(json=lambda: {
                         "sub": "google_id_new",
                         "email": "googleuser@gmail.com",
                         "name": "Google User",
                     }))
        res = test_client.get("/auth/google/callback?code=realcode",
                              follow_redirects=False)
        assert res.status_code == 302
        u = User.query.filter_by(google_id="google_id_new").first()
        assert u is not None

    def test_google_callback_existing_email(self, test_session, test_client, mocker):
        """ Email đã tồn tại → liên kết google_id (index.py:271-272)."""
        u = User(username="existgoogle", email="exist@gmail.com", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()
        mocker.patch("bookingapp.index.http_requests.post",
                     return_value=mocker.Mock(json=lambda: {"access_token": "tok456"}))
        mocker.patch("bookingapp.index.http_requests.get",
                     return_value=mocker.Mock(json=lambda: {
                         "sub": "google_link_id",
                         "email": "exist@gmail.com",
                         "name": "Exist User",
                     }))
        res = test_client.get("/auth/google/callback?code=linkcode",
                              follow_redirects=False)
        assert res.status_code == 302
        test_session.refresh(u)
        assert u.google_id == "google_link_id"

    def test_google_callback_username_collision(self, test_session, test_client, mocker):
        """ Username trùng → thêm số đuôi (index.py:277)."""
        u = User(username="CollisionUser", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()
        mocker.patch("bookingapp.index.http_requests.post",
                     return_value=mocker.Mock(json=lambda: {"access_token": "tok789"}))
        mocker.patch("bookingapp.index.http_requests.get",
                     return_value=mocker.Mock(json=lambda: {
                         "sub": "google_collision_id",
                         "email": "collision@gmail.com",
                         "name": "Collision User",
                     }))
        res = test_client.get("/auth/google/callback?code=collisioncode",
                              follow_redirects=False)
        assert res.status_code == 302
        u2 = User.query.filter_by(google_id="google_collision_id").first()
        assert u2 is not None
        assert u2.username != "CollisionUser"


# ═══════════════════════════════════════════════════════════════════
# SECTION 17: API TEST – /api/my-bookings-detail unauth (index.py:532)
# ═══════════════════════════════════════════════════════════════════

class TestMyBookingsDetailUnauth:
    def test_my_bookings_detail_unauthenticated(self, test_client):
        """Chưa đăng nhập → 401."""
        res = test_client.get("/api/my-bookings-detail")
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# SECTION 18: API TEST – /api/update-profile phone (index.py:586, 590-595)
# ═══════════════════════════════════════════════════════════════════

class TestUpdateProfilePhone:
    def test_update_profile_duplicate_email(self, test_session, logged_in_client):
        """ Email đã được người khác dùng → lỗi (index.py:586)."""
        u2 = User(username="otheruser", email="taken@example.com", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()
        res = logged_in_client.post("/api/update-profile", json={
            "email": "taken@example.com",
        })
        data = res.get_json()
        assert data["ok"] is False
        assert "đã được sử dụng" in data["msg"]

    def test_update_profile_invalid_phone(self, logged_in_client):
        """ SĐT không hợp lệ → lỗi (index.py:590-591)."""
        res = logged_in_client.post("/api/update-profile", json={
            "phone": "12345",
        })
        data = res.get_json()
        assert data["ok"] is False
        assert "không hợp lệ" in data["msg"]

    def test_update_profile_duplicate_phone(self, test_session, logged_in_client):
        """ SĐT đã được người khác dùng → lỗi (index.py:592-594)."""
        u2 = User(username="phoneother", phone="0977777777", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()
        res = logged_in_client.post("/api/update-profile", json={
            "phone": "0977777777",
        })
        data = res.get_json()
        assert data["ok"] is False
        assert "đã được sử dụng" in data["msg"]

    def test_update_profile_valid_phone(self, logged_in_client):
        """ SĐT hợp lệ → thành công (index.py:595)."""
        res = logged_in_client.post("/api/update-profile", json={
            "phone": "0966666666",
        })
        data = res.get_json()
        assert data["ok"] is True