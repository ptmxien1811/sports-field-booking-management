"""
test_integ_booking_review.py – INTEG-05: Booking → Review
Kiểm tra luồng đặt sân ↔ viết đánh giá.
"""

import pytest
from datetime import datetime, timedelta

from bookingapp.models import Booking, Review
from bookingapp.dao import add_review


class TestBookingToReview:
    """INTEG-05: Kiểm tra luồng Booking ↔ Review."""

    def test_booking_enables_review(self, logged_in_client, confirmed_booking, sample_product):
        """
        TC1: Sau khi đặt sân, /api/can-review trả về can_review=True.
        Tích hợp: confirmed_booking → has_booked_product → can-review API.
        """
        res = logged_in_client.get(f"/api/can-review/{sample_product.id}")
        data = res.get_json()
        assert data["can_review"] is True
        assert data["has_booked"] is True
        assert data["has_reviewed"] is False

    def test_review_after_booking_success(self, logged_in_client, confirmed_booking,
                                           sample_product):
        """
        TC2: Đặt sân xong → POST /api/review → review được lưu.
        Tích hợp: Booking → add_review DAO → Review model → DB.
        """
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "Sân rất tốt, dịch vụ chu đáo!",
        })
        data = res.get_json()
        assert res.status_code == 200
        assert data["ok"] is True
        assert data["rating"] == 5

        r = Review.query.filter_by(product_id=sample_product.id).first()
        assert r is not None
        assert r.content == "Sân rất tốt, dịch vụ chu đáo!"

    def test_no_booking_blocks_review(self, logged_in_client, sample_product):
        """
        TC3: Chưa đặt sân → không được review (403).
        Tích hợp: has_booked_product check → 403 response.
        """
        res = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "Cố tình review không đặt",
        })
        assert res.status_code == 403

    def test_review_updates_product_avg_rating(
            self, test_session, logged_in_client, confirmed_booking,
            sample_product, logged_in_user):
        """
        TC4: Sau review, avg_rating của sân cập nhật trong DB.
        Tích hợp: Review saved → Product.avg_rating property.
        """
        logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 4,
            "content": "Khá tốt",
        })
        test_session.refresh(sample_product)
        assert sample_product.avg_rating == 4.0

    def test_double_review_blocked(self, test_session, logged_in_client,
                                    confirmed_booking, sample_product, logged_in_user):
        """
        TC5: Review lần 2 cho cùng sân → 403.
        Tích hợp: has_reviewed_product → block second review.
        """
        logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "Lần 1",
        })
        r2 = logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 3,
            "content": "Lần 2",
        })
        assert r2.status_code == 403

    def test_cancelled_booking_still_allows_review(
            self, test_session, logged_in_user, sample_product):
        """
        TC6: Booking cancelled vẫn cho phép review (đã từng đặt là điều kiện).
        Tích hợp: has_booked_product tính cả status=cancelled.
        """
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

        r, err = add_review(logged_in_user.id, sample_product.id, 3, "Đã đặt nhưng huỷ")
        assert err is None
        assert r is not None

    def test_review_appears_on_venue_detail_page(
            self, logged_in_client, confirmed_booking, sample_product):
        """
        TC7: Review được lưu → hiển thị trên trang /venue/<id>.
        Tích hợp: add_review → DB → venue route → template.
        """
        logged_in_client.post(f"/api/review/{sample_product.id}", json={
            "rating": 5,
            "content": "Tuyệt vời không có gì để chê!",
        })
        res = logged_in_client.get(f"/venue/{sample_product.id}")
        assert res.status_code == 200
        assert "Tuyệt vời".encode("utf-8") in res.data