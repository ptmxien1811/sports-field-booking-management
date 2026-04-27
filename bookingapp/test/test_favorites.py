"""
test_favorite
"""

import pytest
import json
from bookingapp import db
from bookingapp.models import User, Category, Product, Favorite
from bookingapp.dao import toggle_favorite, get_favorites_by_user

# ─── Import fixtures từ test_base ────────────────────────────────────────────
from bookingapp.test.test_base import (
    test_app, test_client, test_session,
    sample_category, sample_product, logged_in_user,
    logged_in_client, admin_user, admin_client,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def another_product(test_session, sample_category):
    """Product thứ 2."""
    p = Product(name="Sân Cầu Lông B1", price=150_000,
                category_id=sample_category.id, active=True)
    test_session.add(p)
    test_session.commit()
    return p


@pytest.fixture
def another_user(test_session):
    """User khác."""
    u = User(username="fav_other", email="favother@ex.com",
             phone="0977777777", auth_type="local")
    u.set_password("Fav@12345")
    test_session.add(u)
    test_session.commit()
    return u


@pytest.fixture
def sample_favorite(test_session, logged_in_user, sample_product):
    """Favorite sẵn có."""
    f = Favorite(user_id=logged_in_user.id, product_id=sample_product.id)
    test_session.add(f)
    test_session.commit()
    return f


# ═══════════════════════════════════════════════════════════════════════════════
#  UNIT TEST – DAO / DB LAYER
# ═══════════════════════════════════════════════════════════════════════════════

class TestFavoriteDAO:

    def test_toggle_favorite_add(self, test_session, logged_in_user, sample_product):
        """toggle_favorite → thêm mới → trả về True."""
        added = toggle_favorite(logged_in_user.id, sample_product.id)
        assert added is True

    def test_toggle_favorite_remove(self, test_session, logged_in_user, sample_product,
                                     sample_favorite):
        """toggle_favorite khi đã có → xóa → trả về False."""
        removed = toggle_favorite(logged_in_user.id, sample_product.id)
        assert removed is False

    def test_toggle_favorite_record_created(self, test_session, logged_in_user, sample_product):
        """ Sau toggle add, bản ghi Favorite tồn tại trong DB."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        fav = Favorite.query.filter_by(
            user_id=logged_in_user.id,
            product_id=sample_product.id
        ).first()
        assert fav is not None

    def test_toggle_favorite_record_deleted(self, test_session, logged_in_user,
                                             sample_product, sample_favorite):
        """Sau toggle remove, bản ghi Favorite bị xóa."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        fav = Favorite.query.filter_by(
            user_id=logged_in_user.id,
            product_id=sample_product.id
        ).first()
        assert fav is None

    def test_toggle_twice_returns_to_original(self, test_session, logged_in_user, sample_product):
        """Toggle 2 lần → quay về trạng thái ban đầu (không có)."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        toggle_favorite(logged_in_user.id, sample_product.id)
        fav = Favorite.query.filter_by(
            user_id=logged_in_user.id,
            product_id=sample_product.id
        ).first()
        assert fav is None

    def test_get_favorites_by_user_empty(self, test_session, logged_in_user):
        """User chưa có favorite → danh sách rỗng."""
        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 0

    def test_get_favorites_by_user_one(self, test_session, logged_in_user,
                                       sample_product, sample_favorite):
        """User có 1 favorite → trả về 1 item."""
        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 1
        assert favs[0].product_id == sample_product.id

    def test_get_favorites_by_user_multiple(self, test_session, logged_in_user,
                                             sample_product, another_product):
        """User có nhiều favorite → trả về đúng số lượng."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        toggle_favorite(logged_in_user.id, another_product.id)
        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 2

    def test_favorites_isolated_by_user(self, test_session, logged_in_user,
                                         another_user, sample_product):
        """Favorite của user A không ảnh hưởng user B."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        favs_other = get_favorites_by_user(another_user.id)
        assert len(favs_other) == 0

    def test_favorite_has_product_relationship(self, test_session, logged_in_user,
                                                sample_product, sample_favorite):
        """Favorite.product trỏ đúng Product."""
        fav = Favorite.query.filter_by(
            user_id=logged_in_user.id,
            product_id=sample_product.id
        ).first()
        assert fav.product.name == sample_product.name

    def test_favorite_count(self, test_session, logged_in_user, sample_product,
                             another_product):
        """Đếm số favorite đúng."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        toggle_favorite(logged_in_user.id, another_product.id)
        count = Favorite.query.filter_by(user_id=logged_in_user.id).count()
        assert count == 2


# ═══════════════════════════════════════════════════════════════════════════════
#  API TEST – api/favorite/<product_id>
# ═══════════════════════════════════════════════════════════════════════════════

class TestFavoriteAPI:

    def _post_favorite(self, client, product_id, app):
        with app.app_context():
            return client.post(f"/api/favorite/{product_id}")

    def test_api_favorite_add_success(self, logged_in_client, sample_product, test_app):
        """POST /api/favorite/<id> → thêm favorite thành công."""
        res = self._post_favorite(logged_in_client, sample_product.id, test_app)
        data = json.loads(res.data)
        assert res.status_code == 200
        assert data["ok"] is True
        assert data["added"] is True

    def test_api_favorite_remove(self, logged_in_client, sample_product,
                                  sample_favorite, test_app):
        """POST lần 2 → xóa favorite."""
        res = self._post_favorite(logged_in_client, sample_product.id, test_app)
        data = json.loads(res.data)
        assert data["added"] is False

    def test_api_favorite_unauthenticated(self, test_client, sample_product, test_app):
        """Chưa đăng nhập → 401."""
        res = self._post_favorite(test_client, sample_product.id, test_app)
        assert res.status_code == 401

    def test_api_favorite_unauthenticated_response(self, test_client, sample_product, test_app):
        """Chưa đăng nhập → ok=False trong response."""
        res = self._post_favorite(test_client, sample_product.id, test_app)
        data = json.loads(res.data)
        assert data["ok"] is False

    def test_api_favorite_toggle_state_correct(self, logged_in_client, sample_product, test_app):
        """Toggle 3 lần: True → False → True."""
        r1 = json.loads(self._post_favorite(logged_in_client, sample_product.id, test_app).data)
        r2 = json.loads(self._post_favorite(logged_in_client, sample_product.id, test_app).data)
        r3 = json.loads(self._post_favorite(logged_in_client, sample_product.id, test_app).data)
        assert r1["added"] is True
        assert r2["added"] is False
        assert r3["added"] is True

    def test_api_my_favorites_count(self, logged_in_client, sample_favorite, test_app):
        """GET /api/my-favorites trả về đúng số lượng."""
        with test_app.app_context():
            res = logged_in_client.get("/api/my-favorites")
        data = json.loads(res.data)
        assert res.status_code == 200
        assert data["favorites"] >= 1

    def test_api_my_favorites_unauthenticated(self, test_client, test_app):
        """ GET /api/my-favorites chưa đăng nhập → 401."""
        with test_app.app_context():
            res = test_client.get("/api/my-favorites")
        assert res.status_code == 401

    def test_api_my_favorites_detail(self, logged_in_client, sample_favorite, test_app):
        """GET /api/my-favorites-detail trả về danh sách."""
        with test_app.app_context():
            res = logged_in_client.get("/api/my-favorites-detail")
        data = json.loads(res.data)
        assert res.status_code == 200
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_api_my_favorites_detail_unauthenticated(self, test_client, test_app):
        """GET /api/my-favorites-detail chưa đăng nhập → 401."""
        with test_app.app_context():
            res = test_client.get("/api/my-favorites-detail")
        assert res.status_code == 401

    def test_api_my_favorites_detail_fields(self, logged_in_client, sample_favorite, test_app):
        """Item trong favorites-detail có đủ fields cần thiết."""
        with test_app.app_context():
            res = logged_in_client.get("/api/my-favorites-detail")
        data = json.loads(res.data)
        item = data["items"][0]
        assert "product_id" in item
        assert "product_name" in item
        assert "price" in item

    def test_favorites_page_accessible(self, logged_in_client, test_app):
        """Trang /favorites accessible."""
        with test_app.app_context():
            res = logged_in_client.get("/favorites", follow_redirects=True)
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TEST
# ═══════════════════════════════════════════════════════════════════════════════

class TestFavoriteIntegration:

    def test_favorite_appears_in_home_page(self, logged_in_client, sample_favorite, test_app):
        """Trang chủ user đã đăng nhập có dữ liệu favorites."""
        with test_app.app_context():
            res = logged_in_client.get("/", follow_redirects=True)
        assert res.status_code == 200

    def test_toggle_then_get_favorites(self, test_session, logged_in_user,
                                        sample_product, another_product):
        """Toggle add 2 sân → get_favorites trả về 2."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        toggle_favorite(logged_in_user.id, another_product.id)
        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 2

    def test_toggle_remove_then_get_favorites(self, test_session, logged_in_user,
                                               sample_product, another_product):
        """Add 2 → remove 1 → get_favorites trả về 1."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        toggle_favorite(logged_in_user.id, another_product.id)
        toggle_favorite(logged_in_user.id, sample_product.id)  # remove
        favs = get_favorites_by_user(logged_in_user.id)
        assert len(favs) == 1
        assert favs[0].product_id == another_product.id

    def test_delete_product_removes_favorite(self, test_session, logged_in_user,
                                              sample_category):
        """Xóa product cascade → Favorite bị xóa."""
        p = Product(name="Cascade Fav Product", price=100,
                    category_id=sample_category.id, active=True)
        test_session.add(p)
        test_session.commit()

        f = Favorite(user_id=logged_in_user.id, product_id=p.id)
        test_session.add(f)
        test_session.commit()
        fav_id = f.id

        test_session.delete(p)
        test_session.commit()

        assert Favorite.query.get(fav_id) is None

    def test_multiple_users_same_product(self, test_session, logged_in_user,
                                          another_user, sample_product):
        """Nhiều user cùng thêm 1 sân vào yêu thích → mỗi người có bản ghi riêng."""
        toggle_favorite(logged_in_user.id, sample_product.id)
        toggle_favorite(another_user.id, sample_product.id)

        count = Favorite.query.filter_by(product_id=sample_product.id).count()
        assert count == 2
