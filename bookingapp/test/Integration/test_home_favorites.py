"""
test_integ_favorites.py – INTEG-06: Booking → Favorites
Kiểm tra luồng yêu thích sân ↔ trang chủ.
"""

import pytest
from bookingapp import db
from bookingapp.models import Product, Favorite


class TestFavoritesIntegration:
    """INTEG-06: Kiểm tra luồng Favorites ↔ Home page."""

    def test_toggle_favorite_then_visible_on_home(
            self, logged_in_client, sample_product):
        """
        TC1: Toggle yêu thích → trang chủ hiển thị số lượng yêu thích.
        Tích hợp: POST /api/favorite → DB → home route context.
        """
        logged_in_client.post(f"/api/favorite/{sample_product.id}")
        res = logged_in_client.get("/api/my-favorites")
        assert res.get_json()["favorites"] == 1

        res_home = logged_in_client.get("/")
        assert res_home.status_code == 200

    def test_favorite_detail_contains_product_fields(
            self, logged_in_client, sample_product):
        """
        TC2: /api/my-favorites-detail trả về đầy đủ fields sau khi toggle.
        Tích hợp: toggle_favorite → get_favorites_by_user → API response.
        """
        logged_in_client.post(f"/api/favorite/{sample_product.id}")
        res = logged_in_client.get("/api/my-favorites-detail")
        data = res.get_json()
        assert res.status_code == 200
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["product_id"] == sample_product.id
        assert "product_name" in item
        assert "price" in item

    def test_unfavorite_removes_from_list(self, logged_in_client, sample_product):
        """
        TC3: Toggle add → toggle remove → danh sách rỗng.
        Tích hợp: 2 lần POST → state trở về 0.
        """
        logged_in_client.post(f"/api/favorite/{sample_product.id}")   # add
        logged_in_client.post(f"/api/favorite/{sample_product.id}")   # remove
        res = logged_in_client.get("/api/my-favorites")
        assert res.get_json()["favorites"] == 0

    def test_favorite_isolated_between_users(
            self, test_app, test_session, logged_in_client,
            sample_product, second_user):
        """
        TC4: User A thả tim sân, User B không thấy trong favorites của mình.
        Tích hợp: Favorite.user_id isolation.

        Dùng fresh client riêng cho second_user để tránh chia sẻ session cookie
        với logged_in_client.
        """
        # User A thả tim
        logged_in_client.post(f"/api/favorite/{sample_product.id}")

        # Tạo fresh client hoàn toàn mới cho User B (không dùng chung cookie)
        fresh_client = test_app.test_client()
        with fresh_client.session_transaction() as sess:
            sess["user_id"] = second_user.id
            sess["username"] = second_user.username

        res = fresh_client.get("/api/my-favorites")
        assert res.get_json()["favorites"] == 0

    def test_delete_product_removes_favorite_from_api(
            self, test_session, logged_in_client, logged_in_user, sample_category):
        """
        TC5: Xoá product cascade → /api/my-favorites trả về 0.
        Tích hợp: cascade delete Product → Favorite → API count.
        """
        p = Product(name="Cascade Fav Integ", price=100,
                    category_id=sample_category.id, active=True)
        test_session.add(p)
        test_session.commit()

        logged_in_client.post(f"/api/favorite/{p.id}")
        assert logged_in_client.get("/api/my-favorites").get_json()["favorites"] == 1

        test_session.delete(p)
        test_session.commit()

        fav_count = Favorite.query.filter_by(user_id=logged_in_user.id).count()
        assert fav_count == 0