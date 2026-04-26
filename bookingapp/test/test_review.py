"""
test_review.py – Kiểm thử đánh giá sân (CR-REVIEW)
Bao gồm: Unit test dao.add_review(), DB constraints, API test /api/review/<id>
"""

import pytest
from bookingapp.models import User, Review, Booking
from bookingapp import db
from bookingapp.dao import add_review, has_booked_product, has_reviewed_product
from datetime import datetime, timedelta

from test_base import (
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking,
)


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: UNIT TEST – Model Review
# ═══════════════════════════════════════════════════════════════════

class TestReviewModel:
    """TC-REVIEW-MODEL: Kiểm tra model Review."""

    def test_review_stars_property(self, test_session, sample_product, logged_in_user):
        """TC1: Property stars trả về ký tự đúng."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=3, content="OK")
        test_session.add(r)
        test_session.commit()
        assert r.stars == "★★★☆☆"

    def test_review_stars_5(self, test_session, sample_product, logged_in_user):
        """TC2: Rating 5 → 5 sao đầy."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="Tuyệt!")
        test_session.add(r)
        test_session.commit()
        assert r.stars == "★★★★★"

    def test_review_stars_1(self, test_session, sample_product, logged_in_user):
        """TC3: Rating 1 → 1 sao."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=1, content="Tệ")
        test_session.add(r)
        test_session.commit()
        assert r.stars == "★☆☆☆☆"

    def test_review_date_str_today(self, test_session, sample_product, logged_in_user):
        """TC4: Review vừa tạo → date_str = 'Hôm nay'."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=4, content="Fresh")
        test_session.add(r)
        test_session.commit()
        assert r.date_str == "Hôm nay"

    def test_review_date_str_days_ago(self, test_session, sample_product, logged_in_user):
        """TC5: Review 3 ngày trước → '3 ngày trước'."""
        past = datetime.now() - timedelta(days=3)
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=4, content="Old", created_at=past)
        test_session.add(r)
        test_session.commit()
        assert "ngày trước" in r.date_str

    def test_review_date_str_weeks_ago(self, test_session, sample_product, logged_in_user):
        """TC6: Review 2 tuần trước → 'N tuần trước'."""
        past = datetime.now() - timedelta(weeks=2)
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=3, content="Weeks ago", created_at=past)
        test_session.add(r)
        test_session.commit()
        assert "tuần trước" in r.date_str

    def test_review_relationship_to_user(self, test_session, sample_product, logged_in_user):
        """TC7: Review.user trỏ về user đúng."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="Good")
        test_session.add(r)
        test_session.commit()
        assert r.user.username == logged_in_user.username

    def test_review_relationship_to_product(self, test_session, sample_product, logged_in_user):
        """TC8: Review.product trỏ về product đúng."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="Good")
        test_session.add(r)
        test_session.commit()
        assert r.product.name == sample_product.name


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: UNIT TEST – dao helpers
# ═══════════════════════════════════════════════════════════════════

class TestReviewHelperDAO:
    """TC-REVIEW-HELPER: has_booked_product, has_reviewed_product."""

    def test_has_booked_true(self, test_session, logged_in_user, sample_product,
                              confirmed_booking):
        """TC1: Đã đặt sân → True."""
        assert has_booked_product(logged_in_user.id, sample_product.id) is True

    def test_has_booked_false(self, test_session, logged_in_user, sample_product):
        """TC2: Chưa đặt → False."""
        assert has_booked_product(logged_in_user.id, sample_product.id) is False

    def test_has_booked_counts_cancelled(self, test_session, logged_in_user, sample_product):
        """TC3: Booking cancelled vẫn được tính (điều kiện viết review)."""
        tomorrow = datetime.now() + timedelta(days=1)
        day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            slot_label="08:00 - 09:00",
            date=day_start,
            start_time=tomorrow.replace(hour=8),
            end_time=tomorrow.replace(hour=9),
            status="cancelled",
        )
        test_session.add(b)
        test_session.commit()
        assert has_booked_product(logged_in_user.id, sample_product.id) is True

    def test_has_reviewed_false(self, test_session, logged_in_user, sample_product):
        """TC4: Chưa review → False."""
        assert has_reviewed_product(logged_in_user.id, sample_product.id) is False

    def test_has_reviewed_true(self, test_session, logged_in_user, sample_product,
                                confirmed_booking):
        """TC5: Đã review → True."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="Nice")
        test_session.add(r)
        test_session.commit()
        assert has_reviewed_product(logged_in_user.id, sample_product.id) is True


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: UNIT TEST – dao.add_review()
# ═══════════════════════════════════════════════════════════════════

class TestAddReviewDAO:
    """TC-REVIEW-DAO: Kiểm tra hàm add_review."""

    def test_add_review_success(self, test_session, logged_in_user, sample_product,
                                 confirmed_booking):
        """TC1: Đã đặt, chưa review → thành công."""
        r, err = add_review(logged_in_user.id, sample_product.id, 5, "Sân rất tốt!")
        assert err is None
        assert r is not None
        assert r.rating == 5
        assert r.content == "Sân rất tốt!"

    def test_add_review_not_booked(self, test_session, logged_in_user, sample_product):
        """TC2: Chưa đặt sân → lỗi."""
        r, err = add_review(logged_in_user.id, sample_product.id, 5, "Test")
        assert r is None
        assert "đã đặt" in err

    def test_add_review_already_reviewed(self, test_session, logged_in_user, sample_product,
                                          confirmed_booking):
        """TC3: Đã review rồi → không cho review lần 2."""
        add_review(logged_in_user.id, sample_product.id, 4, "Lần 1")
        r2, err2 = add_review(logged_in_user.id, sample_product.id, 3, "Lần 2")
        assert r2 is None
        assert "đã đánh giá" in err2

    def test_add_review_rating_clamped_max_5(self, test_session, logged_in_user,
                                              sample_product, confirmed_booking):
        """TC4: Rating > 5 → clamp về 5."""
        r, err = add_review(logged_in_user.id, sample_product.id, 10, "Out of range")
        assert err is None
        assert r.rating == 5

    def test_add_review_rating_clamped_min_1(self, test_session, logged_in_user,
                                              sample_product, confirmed_booking):
        """TC5: Rating < 1 → clamp về 1."""
        r, err = add_review(logged_in_user.id, sample_product.id, 0, "Zero")
        assert err is None
        assert r.rating == 1

    @pytest.mark.parametrize("rating", [1, 2, 3, 4, 5])
    def test_add_review_valid_ratings(self, test_session, sample_category, rating):
        """TC6: Tất cả rating 1-5 đều được chấp nhận."""
        u = User(username=f"ruser_{rating}", auth_type="local")
        u.set_password("Test@1234")
        c = Category(name=f"CatR_{rating}")
        test_session.add_all([u, c])
        test_session.commit()

        p = Product(name=f"ProdR_{rating}", price=100_000, category_id=c.id)
        test_session.add(p)
        test_session.commit()

        tomorrow = datetime.now() + timedelta(days=1)
        day_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        b = Booking(
            user_id=u.id, product_id=p.id, slot_label="08:00 - 09:00",
            date=day_start, start_time=tomorrow.replace(hour=8),
            end_time=tomorrow.replace(hour=9), status="confirmed",
        )
        test_session.add(b)
        test_session.commit()

        r, err = add_review(u.id, p.id, rating, f"Rating {rating}")
        assert err is None
        assert r.rating == rating

    def test_add_review_updates_product_avg_rating(self, test_session, logged_in_user,
                                                    sample_product, confirmed_booking):
        """TC7: Sau khi review, avg_rating của product cập nhật."""
        add_review(logged_in_user.id, sample_product.id, 4, "Nice")
        test_session.refresh(sample_product)
        assert sample_product.avg_rating == 4.0


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: API TEST – POST /api/review/<product_id>
# ═══════════════════════════════════════════════════════════════════

class TestReviewAPI:
    """TC-REVIEW-API: POST /api/review/<id>"""

    def test_review_unauthenticated(self, test_client, sample_product):
        """TC1: Chưa đăng nhập → 401."""
        res = test_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "Test review",
        })
        assert res.status_code == 401
        data = res.get_json()
        assert data["ok"] is False

    def test_review_success(self, logged_in_client, confirmed_booking, sample_product):
        """TC2: Đã đặt, chưa review → thành công."""
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "Sân rất đẹp và sạch!",
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["ok"] is True
        assert data["rating"] == 5
        assert "author" in data
        assert "stars" in data
        assert "date_str" in data

    def test_review_not_booked(self, logged_in_client, sample_product):
        """TC3: Chưa đặt sân → 403."""
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 4,
            "content": "Review without booking",
        })
        assert res.status_code == 403
        data = res.get_json()
        assert data["ok"] is False

    def test_review_duplicate(self, test_session, logged_in_client, confirmed_booking,
                               sample_product, logged_in_user):
        """TC4: Review lần 2 → 403."""
        r = Review(product_id=sample_product.id, user_id=logged_in_user.id,
                   rating=5, content="First review")
        test_session.add(r)
        test_session.commit()

        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 3,
            "content": "Second review",
        })
        assert res.status_code == 403

    def test_review_empty_content(self, logged_in_client, confirmed_booking, sample_product):
        """TC5: Nội dung rỗng → 400."""
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "",
        })
        assert res.status_code == 400
        data = res.get_json()
        assert data["ok"] is False

    def test_review_response_contains_all_fields(self, logged_in_client, confirmed_booking,
                                                   sample_product):
        """TC6: Response có đủ fields: ok, author, rating, stars, content, date_str."""
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 4,
            "content": "Hài lòng với dịch vụ",
        })
        data = res.get_json()
        for field in ["ok", "author", "rating", "stars", "content", "date_str"]:
            assert field in data, f"Missing field: {field}"

    def test_review_default_rating_is_5(self, logged_in_client, confirmed_booking, sample_product):
        """TC7: Không truyền rating → mặc định 5."""
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "content": "Default rating test",
        })
        data = res.get_json()
        assert data["ok"] is True
        assert data["rating"] == 5

    def test_review_stars_format(self, logged_in_client, confirmed_booking, sample_product):
        """TC8: Stars có đúng 5 ký tự (★/☆ kết hợp)."""
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 3,
            "content": "Three stars",
        })
        data = res.get_json()
        assert data["ok"] is True
        assert len(data["stars"]) == 5
        assert data["stars"] == "★★★☆☆"