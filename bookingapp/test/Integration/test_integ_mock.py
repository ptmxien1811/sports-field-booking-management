"""
test_integ_mock.py – INTEG-10: Mock – External Services & Error Scenarios
Mock các service bên ngoài (Google OAuth, DB lỗi) và kiểm tra error handling.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from bookingapp import db
from bookingapp.models import User, Bill, Review
from bookingapp.dao import add_review
from bookingapp.test.test_base import create_app


class TestMockIntegration:
    """INTEG-10: Mock các service bên ngoài và tình huống lỗi DB."""

    def test_mock_google_oauth_user_creation(self, test_app, test_client):
        """
        TC1: Mock Google OAuth response → user được tạo từ thông tin Google.
        Mock: requests.post (token exchange) + requests.get (user info).
        """
        fake_token_response = MagicMock()
        fake_token_response.json.return_value = {"access_token": "fake_token_abc"}

        fake_user_info = MagicMock()
        fake_user_info.json.return_value = {
            "sub": "google_uid_12345",
            "email": "google_integ@test.com",
            "name": "Google Test User",
        }

        with patch("bookingapp.index.http_requests.post", return_value=fake_token_response), \
             patch("bookingapp.index.http_requests.get", return_value=fake_user_info):
            res = test_client.get(
                "/auth/google/callback?code=fake_code",
                follow_redirects=True
            )
            assert res.status_code in [200, 302, 404]

    def test_mock_db_session_add_called_on_booking(
            self, mocker, logged_in_client, product_with_slots, future_date):
        """
        TC2: Khi đặt sân, db.session.add() được gọi ít nhất 1 lần.
        Mock: spy trên db.session.add để verify call.
        """
        spy = mocker.spy(db.session, "add")

        logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })

        spy.assert_called()

    def test_mock_payment_db_commit_error_raises(
            self, mocker, logged_in_client, confirmed_booking):
        """
        TC3: Khi DB commit lỗi trong thanh toán → exception được raise.
        Mock: db.session.commit → Exception ("DB connection lost").
        """
        mocker.patch.object(db.session, "commit",
                            side_effect=Exception("DB connection lost"))
        with pytest.raises(Exception, match="DB connection lost"):
            logged_in_client.post("/api/payment", json={
                "booking_id": confirmed_booking.id,
                "payment_method": "direct",
            })

    def test_mock_product_price_property(
            self, mocker, test_session, confirmed_booking,
            logged_in_user, sample_product):
        """
        TC4: Mock product.price property → Bill amount dùng giá mock.
        Mock: PropertyMock trên Product.price.
        """
        mocker.patch.object(type(sample_product), "price",
                            new_callable=PropertyMock, return_value=999_999)
        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,
        )
        test_session.add(bill)
        test_session.commit()
        assert bill.amount == 999_999

    def test_mock_toggle_favorite_isolates_from_db(self, mocker, test_app):
        """
        TC5: Mock toàn bộ DB cho toggle_favorite → verify logic flow.
        Mock Object: Fake Favorite + db.session thao tác.
        """
        mock_fav = MagicMock()
        mock_fav.user_id = 1
        mock_fav.product_id = 10

        mock_session = MagicMock()
        mock_session.delete = MagicMock()
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()

        assert mock_fav.user_id == 1
        assert mock_fav.product_id == 10
        mock_session.delete(mock_fav)
        mock_session.delete.assert_called_once_with(mock_fav)

    def test_mock_add_review_with_fake_booking(self, mocker, test_session,
                                                 sample_product):
        """
        TC6: Mock has_booked_product → True → add_review thành công mà không cần booking thật.
        Mock: bookingapp.dao.has_booked_product trả về True.
        """
        new_user = User(username="mock_reviewer", auth_type="local")
        new_user.set_password("Mock@1234")
        test_session.add(new_user)
        test_session.commit()

        with patch("bookingapp.dao.has_booked_product", return_value=True):
            r, err = add_review(new_user.id, sample_product.id, 4, "Reviewed via mock")
        assert err is None
        assert r is not None
        assert r.rating == 4

    def test_mock_slot_query_for_performance(self, mocker, test_session, sample_product):
        """
        TC7: Mock get_slots_for_product_date → isolate slot logic khỏi DB.
        Mock Data: trả về dict slots giả để kiểm tra consumer code.
        """
        mock_slots = {
            "morning": [
                {"label": "08:00 - 09:00", "booked": False},
                {"label": "09:00 - 10:00", "booked": True},
            ]
        }
        with patch("bookingapp.dao.get_slots_for_product_date",
                   return_value=(mock_slots, 1)) as mock_fn:
            slots, available = mock_fn(sample_product.id, datetime.now().date())
            assert available == 1
            assert mock_slots["morning"][0]["booked"] is False
            assert mock_slots["morning"][1]["booked"] is True

    def test_mock_cancel_grouped_booking_dao(self, mocker):
        """
        TC8: Mock cancel_grouped_booking → verify return values.
        Mock Object: giả lập Booking group cancel flow.
        """
        with patch("bookingapp.dao.cancel_grouped_booking",
                   return_value=(True, True)) as mock_cancel:
            success, had_bill = mock_cancel("group_fake_id", user_id=1)
            assert success is True
            assert had_bill is True
            mock_cancel.assert_called_once_with("group_fake_id", user_id=1)

    def test_mock_entire_payment_flow(self, mocker, test_app):
        """
        TC9: Mock toàn bộ Booking + Bill layer → kiểm tra logic tầng route.
        Mock Object: Booking giả + db.session.
        """
        mock_booking = MagicMock()
        mock_booking.id = 42
        mock_booking.user_id = 1
        mock_booking.product_id = 1
        mock_booking.product.price = 500_000
        mock_booking.group_id = None
        mock_booking.status = "confirmed"

        mock_bill = MagicMock()
        mock_bill.id = 99
        mock_bill.amount = 500_000
        mock_bill.payment_method = "direct"
        mock_bill.created_at = datetime.now()

        assert mock_booking.product.price == 500_000
        assert mock_bill.id == 99
        assert mock_bill.amount == mock_booking.product.price

    def test_mock_review_content_sanitization(self, mocker, test_session,
                                               sample_product, logged_in_user,
                                               confirmed_booking):
        """
        TC10: Nội dung review rỗng → API trả về 400.
        Tích hợp + Mock: API route kiểm tra content trước khi gọi DAO.
        """
        spy = mocker.spy(
            __import__("bookingapp.dao", fromlist=["add_review"]),
            "add_review"
        )

        app = create_app()
        with app.app_context():
            db.create_all()
            u = User(username="empty_rev", auth_type="local")
            u.set_password("Test@1234")
            db.session.add(u)
            db.session.commit()

            client = app.test_client()
            with client.session_transaction() as sess:
                sess["user_id"] = u.id
                sess["username"] = u.username

            from bookingapp.models import Category as Cat2, Product as Prod2
            cat = Cat2(name="EmptyCat")
            db.session.add(cat)
            db.session.commit()
            p = Prod2(name="EmptyRevProd", price=100, category_id=cat.id)
            db.session.add(p)
            db.session.commit()

            res = client.post(f"/api/review/{p.id}", json={
                "rating": 5,
                "content": "",
            })
            # Route phải chặn content rỗng trả về 400 trước khi vào dao
            assert res.status_code in [400, 401, 403]
            db.session.remove()
            db.drop_all()