"""
test_home.py – Kiểm thử trang chủ, yêu thích, thanh toán (CR600-HOME / CR500-FAV)
Bao gồm: GET /, /explore, /featured, /favorites, /api/favorite, /api/payment
"""

import pytest
from bookingapp.models import Product, Category, Favorite, Bill, User
from bookingapp import db
from bookingapp.dao import get_favorites_by_user, toggle_favorite
from datetime import datetime, timedelta

from bookingapp.test.test_base import (
    test_app,
    test_client,
    test_session,
    sample_category,
    sample_product,
    logged_in_user,
    admin_user,
    logged_in_client,
    admin_client,
    confirmed_booking,
    paid_booking,
)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: API TEST – GET / (Trang chủ)
# ═══════════════════════════════════════════════════════════════════

class TestHomePage:
    """TC-HOME-PAGE: GET /"""

    def test_home_returns_200(self, test_client):
        """TC1: Trang chủ trả về 200."""
        res = test_client.get("/")
        assert res.status_code == 200

    def test_home_shows_active_products(self, test_client, sample_product):
        """TC2: Hiển thị sân active."""
        res = test_client.get("/")
        assert res.status_code == 200
        assert sample_product.name.encode() in res.data

    def test_home_hides_inactive_products(self, test_session, test_client, sample_category):
        """TC3: Không hiển thị sân inactive."""
        p = Product(name="Sân Ẩn", price=100_000, category_id=sample_category.id, active=False)
        test_session.add(p)
        test_session.commit()

        res = test_client.get("/")
        assert "Sân Ẩn".encode() not in res.data

    def test_home_logged_in_user_context(self, logged_in_client, logged_in_user):
        """TC4: User đăng nhập → username trong context."""
        res = logged_in_client.get("/")
        assert res.status_code == 200
        assert logged_in_user.username.encode() in res.data

    def test_home_guest_no_username(self, test_client):
        """TC5: Guest → không có username trong session."""
        res = test_client.get("/")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: API TEST – Static pages
# ═══════════════════════════════════════════════════════════════════

class TestStaticPages:
    """TC-HOME-STATIC: /explore, /featured, /favorites, /account"""

    def test_explore_page(self, test_client):
        """TC1: /explore trả về 200."""
        res = test_client.get("/explore")
        assert res.status_code == 200

    def test_featured_page(self, test_client, sample_product):
        """TC2: /featured trả về 200 và hiển thị sản phẩm."""
        res = test_client.get("/featured")
        assert res.status_code == 200

    def test_favorites_rendered_on_home(self, logged_in_client):
        """TC3: Favorites section nằm trên trang chủ."""
        res = logged_in_client.get("/", follow_redirects=True)
        assert res.status_code == 200

    def test_account_page_unauthenticated_redirect(self, test_client):
        """TC4: /account chưa đăng nhập → redirect login."""
        res = test_client.get("/account", follow_redirects=False)
        assert res.status_code == 302
        assert "login" in res.headers.get("Location", "")

    def test_account_page_authenticated(self, logged_in_client):
        """TC5: /account đã đăng nhập → 200."""
        res = logged_in_client.get("/account")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: UNIT TEST – DB Favorite model
# ═══════════════════════════════════════════════════════════════════

class TestFavoriteModel:
    """TC-FAV-MODEL: Kiểm tra model Favorite."""

    def test_create_favorite(self, test_session, logged_in_user, sample_product):
        """TC1: Thêm yêu thích thành công."""
        fav = Favorite(user_id=logged_in_user.id, product_id=sample_product.id)
        test_session.add(fav)
        test_session.commit()

        found = Favorite.query.filter_by(
            user_id=logged_in_user.id, product_id=sample_product.id
        ).first()
        assert found is not None

    def test_favorite_relationship_product(self, test_session, logged_in_user, sample_product):
        """TC2: Favorite.product trỏ đúng."""
        fav = Favorite(user_id=logged_in_user.id, product_id=sample_product.id)
        test_session.add(fav)
        test_session.commit()
        assert fav.product.name == sample_product.name

    def test_favorite_relationship_user(self, test_session, logged_in_user, sample_product):
        """TC3: Favorite.user trỏ đúng."""
        fav = Favorite(user_id=logged_in_user.id, product_id=sample_product.id)
        test_session.add(fav)
        test_session.commit()
        assert fav.user.username == logged_in_user.username

    def test_favorite_cascade_delete_on_product(self, test_session, logged_in_user, sample_product):
        """TC4: Xóa Product → cascade xóa Favorite."""
        fav = Favorite(user_id=logged_in_user.id, product_id=sample_product.id)
        test_session.add(fav)
        test_session.commit()
        fav_id = fav.id

        test_session.delete(sample_product)
        test_session.commit()

        assert Favorite.query.get(fav_id) is None


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: UNIT TEST – dao.toggle_favorite()
# ═══════════════════════════════════════════════════════════════════

class TestToggleFavoriteDAO:
    """TC-FAV-DAO: Kiểm tra hàm toggle_favorite."""

    def test_toggle_add_favorite(self, test_session, logged_in_user, sample_product):
        """TC1: Toggle lần đầu → thêm yêu thích (added=True)."""
        added = toggle_favorite(logged_in_user.id, sample_product.id)
        assert added is True
        fav = Favorite.query.filter_by(
            user_id=logged_in_user.id, product_id=sample_product.id
        ).first()
        assert fav is not None

    def test_toggle_remove_favorite(self, test_session, logged_in_user, sample_product):
        """TC2: Toggle lần 2 → xóa yêu thích (added=False)."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        added = toggle_favorite(logged_in_user.id, sample_product.id)
        assert added is False
        fav = Favorite.query.filter_by(
            user_id=logged_in_user.id, product_id=sample_product.id
        ).first()
        assert fav is None

    def test_toggle_multiple_products(self, test_session, logged_in_user, sample_category):
        """TC3: Toggle nhiều sân độc lập."""
        p1 = Product(name="SanFav1", price=100_000, category_id=sample_category.id)
        p2 = Product(name="SanFav2", price=100_000, category_id=sample_category.id)
        test_session.add_all([p1, p2])
        test_session.commit()

        toggle_favorite(logged_in_user.id, p1.id)
        toggle_favorite(logged_in_user.id, p2.id)

        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 2

    def test_get_favorites_by_user(self, test_session, logged_in_user, sample_product):
        """TC4: get_favorites_by_user trả về đúng danh sách."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 1
        assert favs[0].product_id == sample_product.id

    def test_get_favorites_empty(self, test_session, logged_in_user):
        """TC5: Chưa có yêu thích nào → list rỗng."""
        favs = get_favorites_by_user(logged_in_user.id)
        assert favs == []


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: API TEST – POST /api/favorite/<product_id>
# ═══════════════════════════════════════════════════════════════════

class TestFavoriteAPI:
    """TC-FAV-API: POST /api/favorite/<id>"""

    def test_favorite_unauthenticated(self, test_client, sample_product):
        """TC1: Chưa đăng nhập → 401."""
        res = test_client.post(f"/api/favorite/{sample_product.id}")
        assert res.status_code == 401
        data = res.get_json()
        assert data["ok"] is False

    def test_favorite_add(self, logged_in_client, sample_product):
        """TC2: Toggle thêm yêu thích → added=True."""
        res = logged_in_client.post(f"/api/favorite/{sample_product.id}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert data["added"] is True

    def test_favorite_remove(self, logged_in_client, sample_product):
        """TC3: Toggle lần 2 → added=False."""
        logged_in_client.post(f"/api/favorite/{sample_product.id}")  # add
        res = logged_in_client.post(f"/api/favorite/{sample_product.id}")  # remove
        data = res.get_json()
        assert data["added"] is False

    def test_my_favorites_count(self, logged_in_client, sample_product):
        """TC4: /api/my-favorites trả về số lượng đúng."""
        logged_in_client.post(f"/api/favorite/{sample_product.id}")
        res = logged_in_client.get("/api/my-favorites")
        data = res.get_json()
        assert data["favorites"] == 1

    def test_my_favorites_detail(self, logged_in_client, sample_product):
        """TC5: /api/my-favorites-detail trả về đúng cấu trúc."""
        logged_in_client.post(f"/api/favorite/{sample_product.id}")
        res = logged_in_client.get("/api/my-favorites-detail")
        data = res.get_json()
        assert "items" in data
        assert len(data["items"]) == 1
        item = data["items"][0]
        for field in ["product_id", "product_name", "image", "price"]:
            assert field in item

    def test_my_favorites_unauthenticated(self, test_client):
        """TC6: Chưa đăng nhập → 401."""
        res = test_client.get("/api/my-favorites")
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: DB TEST – Bill model
# ═══════════════════════════════════════════════════════════════════

class TestBillModel:
    """TC-BILL-MODEL: Kiểm tra model Bill (hóa đơn thanh toán)."""

    def test_bill_created(self, test_session, logged_in_user, sample_product, confirmed_booking):
        """TC1: Tạo Bill thành công."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
            payment_method="direct",
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.id is not None

    def test_bill_str(self, test_session, logged_in_user, sample_product, confirmed_booking):
        """TC2: __str__ trả về format đúng."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=300_000,
            payment_method="direct",
        )
        test_session.add(bill)
        test_session.commit()
        assert f"Bill #{bill.id}" in str(bill)
        assert "300000" in str(bill)

    def test_bill_relationship_booking(self, test_session, logged_in_user,
                                        sample_product, confirmed_booking):
        """TC3: Bill.booking trỏ đúng."""
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.booking.id == confirmed_booking.id


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: API TEST – Payment routes
# ═══════════════════════════════════════════════════════════════════

class TestPaymentAPI:
    """TC-PAY-API: /payment/<id> và /api/payment"""

    def test_payment_page_unauthenticated(self, test_client, confirmed_booking):
        """TC1: Chưa đăng nhập → redirect login."""
        res = test_client.get(f"/payment/{confirmed_booking.id}", follow_redirects=False)
        assert res.status_code == 302
        assert "login" in res.headers.get("Location", "")

    def test_payment_page_authenticated(self, logged_in_client, confirmed_booking):
        """TC2: Đã đăng nhập → 200."""
        res = logged_in_client.get(f"/payment/{confirmed_booking.id}")
        assert res.status_code == 200

    def test_payment_page_wrong_user(self, test_session, test_client,
                                      confirmed_booking):
        """TC3: Booking của user khác → redirect."""
        u2 = User(username="other_pay", auth_type="local")
        u2.set_password("Test@1234")
        test_session.add(u2)
        test_session.commit()

        with test_client.session_transaction() as sess:
            sess["user_id"] = u2.id
            sess["username"] = u2.username

        res = test_client.get(f"/payment/{confirmed_booking.id}", follow_redirects=False)
        assert res.status_code == 302

    def test_api_payment_success(self, logged_in_client, confirmed_booking):
        """TC4: Thanh toán thành công → ok=True, bill_id trả về."""
        res = logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })
        data = res.get_json()
        assert data["ok"] is True
        assert "bill_id" in data

    def test_api_payment_duplicate(self, logged_in_client, paid_booking):
        """TC5: Thanh toán lần 2 → lỗi 400."""
        booking, bill = paid_booking
        res = logged_in_client.post("/api/payment", json={
            "booking_id": booking.id,
            "payment_method": "direct",
        })
        assert res.status_code == 400
        data = res.get_json()
        assert data["ok"] is False

    def test_api_payment_unauthenticated(self, test_client, confirmed_booking):
        """TC6: Chưa đăng nhập → 401."""
        res = test_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "direct",
        })
        assert res.status_code == 401

    def test_api_payment_nonexistent_booking(self, logged_in_client):
        """TC7: Booking không tồn tại → 404."""
        res = logged_in_client.post("/api/payment", json={
            "booking_id": 99999,
            "payment_method": "direct",
        })
        assert res.status_code == 404

    def test_api_payment_online_method(self, logged_in_client, confirmed_booking):
        """TC8: Thanh toán online cũng thành công."""
        res = logged_in_client.post("/api/payment", json={
            "booking_id": confirmed_booking.id,
            "payment_method": "online",
        })
        data = res.get_json()
        assert data["ok"] is True

    def test_payment_page_shows_paid_status(self, logged_in_client, paid_booking):
        """TC9: Trang thanh toán hiển thị trạng thái đã thanh toán."""
        booking, bill = paid_booking
        res = logged_in_client.get(f"/payment/{booking.id}")
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# SECTION 8: API TEST – Account stats
# ═══════════════════════════════════════════════════════════════════

class TestAccountStats:
    """TC-ACCT-STATS: /api/my-bookings, /api/my-favorites, /api/my-reviews"""

    def test_my_bookings_count_correct(self, logged_in_client, confirmed_booking):
        """TC1: Đúng số booking confirmed."""
        res = logged_in_client.get("/api/my-bookings")
        data = res.get_json()
        assert data["bookings"] == 1

    def test_my_reviews_count_correct(self, test_session, logged_in_client,
                                       confirmed_booking, sample_product, logged_in_user):
        """TC2: Đúng số review."""
        from bookingapp.models import Review
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="Good")
        test_session.add(r)
        test_session.commit()

        res = logged_in_client.get("/api/my-reviews")
        data = res.get_json()
        assert data["reviews"] == 1

    def test_my_reviews_unauthenticated(self, test_client):
        """TC3: Chưa đăng nhập → 401."""
        res = test_client.get("/api/my-reviews")
        assert res.status_code == 401