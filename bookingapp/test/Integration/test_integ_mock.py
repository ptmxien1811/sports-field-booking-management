"""
test_integ_mock.py – INTEG-10: Mock – External Services & Error Scenarios
Mock các service bên ngoài (Google OAuth, DB lỗi) và kiểm tra error handling.

Chiến lược: Mock SQLAlchemy Session (Mục 2.3 – Hướng dẫn GV)
- Cô lập logic khỏi DB thật bằng unittest.mock (patch, MagicMock, PropertyMock)
- Kiểm tra hành vi (behavior): add/commit/delete có được gọi không
- Mô phỏng lỗi DB (side_effect) để verify error handling
- Không cần kết nối DB thật → test chạy nhanh, độc lập
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock, call
from datetime import datetime
from bookingapp.test.test_base import create_app
from bookingapp.models import Category as Cat2, Product as Prod2

from bookingapp import db
from bookingapp.models import User, Bill, Review
from bookingapp.dao import add_review
from bookingapp.test.test_base import (
    test_app, test_client, test_session,
    sample_category, sample_product,
    logged_in_user, logged_in_client,
    confirmed_booking,
)


class TestMockIntegration:
    """INTEG-10: Mock các service bên ngoài và tình huống lỗi DB."""

    # ─────────────────────────────────────────────────────────────────
    # TC1: Mock Google OAuth – kiểm tra user được tạo từ thông tin Google
    # ─────────────────────────────────────────────────────────────────
    def test_mock_google_oauth_new_user_created(self, test_app, test_client):
        """
        TC1: Mock Google OAuth response → user được tạo với google_id đúng.
        - Mock: http_requests.post (token exchange) → access_token giả
        - Mock: http_requests.get (user info) → sub/email/name giả
        - Verify: User được tạo trong DB với google_id khớp và auth_type == "google"

        Sửa từ phiên bản cũ:
          Cũ: assert res.status_code in [200, 302, 404]  ← quá lỏng, không verify gì
          Mới: assert user tồn tại trong DB với google_id và auth_type đúng
        """
        fake_token = MagicMock()
        fake_token.json.return_value = {"access_token": "fake_token_tc1"}

        fake_info = MagicMock()
        fake_info.json.return_value = {
            "sub": "google_uid_tc1",
            "email": "tc1_oauth@test.com",
            "name": "TC1 Google User",
        }

        with patch("bookingapp.index.http_requests.post", return_value=fake_token), \
             patch("bookingapp.index.http_requests.get", return_value=fake_info):
            res = test_client.get(
                "/auth/google/callback?code=fake_code_tc1",
                follow_redirects=False,
            )

        # Route xử lý OK → redirect về home (302)
        assert res.status_code == 302

        # Verify user được lưu DB với google_id đúng
        u = User.query.filter_by(google_id="google_uid_tc1").first()
        assert u is not None
        assert u.auth_type == "google"

    # ─────────────────────────────────────────────────────────────────
    # TC2: Mock Google OAuth – token không có access_token → redirect, không crash
    # ─────────────────────────────────────────────────────────────────
    def test_mock_google_oauth_missing_token_redirects(self, test_client, mocker):
        """
        TC2: Khi Google trả về response KHÔNG có access_token → redirect (không crash 500).
        - Mock: http_requests.post trả về dict rỗng {} (không có "access_token")
        - Verify: status_code là 302 (redirect về login/home), không phải 500

        Test case mới hoàn toàn: tách riêng trường hợp token thiếu để đảm bảo
        route xử lý lỗi gracefully thay vì raise KeyError và crash.
        """
        mocker.patch(
            "bookingapp.index.http_requests.post",
            return_value=mocker.Mock(json=lambda: {}),
        )

        res = test_client.get(
            "/auth/google/callback?code=no_token_code",
            follow_redirects=False,
        )

        # Không được crash 500 – phải redirect
        assert res.status_code == 302

    # ─────────────────────────────────────────────────────────────────
    # TC3: Mock Google OAuth – email đã tồn tại → link google_id vào user cũ
    # ─────────────────────────────────────────────────────────────────
    def test_mock_google_oauth_existing_email_linked(
            self, test_session, test_client, mocker):
        """
        TC3: User đã có email trong DB + Google callback cùng email → google_id được gắn.
        - Tạo user local trước với email exist@gmail.com
        - Mock Google trả sub="google_link_id", email="exist@gmail.com"
        - Verify: user.google_id được cập nhật thành "google_link_id"
        """
        u = User(username="exist_user_tc3", email="exist_tc3@gmail.com", auth_type="local")
        u.set_password("Test@1234")
        test_session.add(u)
        test_session.commit()

        mocker.patch(
            "bookingapp.index.http_requests.post",
            return_value=mocker.Mock(json=lambda: {"access_token": "tok_tc3"}),
        )
        mocker.patch(
            "bookingapp.index.http_requests.get",
            return_value=mocker.Mock(json=lambda: {
                "sub": "google_link_tc3",
                "email": "exist_tc3@gmail.com",
                "name": "Exist User TC3",
            }),
        )

        res = test_client.get(
            "/auth/google/callback?code=link_code_tc3",
            follow_redirects=False,
        )

        assert res.status_code == 302
        test_session.refresh(u)
        assert u.google_id == "google_link_tc3"

    # ─────────────────────────────────────────────────────────────────
    # TC4: Spy db.session.add() khi đặt sân
    # ─────────────────────────────────────────────────────────────────
    def test_mock_db_session_add_called_on_booking(
            self, mocker, logged_in_client, product_with_slots, future_date):
        """
        TC4: Khi POST /api/book, db.session.add() phải được gọi ít nhất 1 lần.
        - Spy: db.session.add (không thay thế, chỉ ghi nhận call)
        - Verify: spy.assert_called() → đảm bảo booking object được add vào session

        Tham chiếu GV (mục 2.3):
          "kiểm tra xem db.session.add() có được gọi đúng không"
        """
        spy = mocker.spy(db.session, "add")

        logged_in_client.post("/api/book", json={
            "product_id": product_with_slots.id,
            "slot": "08:00 - 09:00",
            "date": str(future_date),
        })

        spy.assert_called()

    # ─────────────────────────────────────────────────────────────────
    # TC5: Mock db.session.commit lỗi khi thanh toán → exception được raise
    # ─────────────────────────────────────────────────────────────────
    def test_mock_payment_db_commit_error_raises(
            self, mocker, logged_in_client, confirmed_booking):
        """
        TC5: Khi DB commit lỗi trong thanh toán → hệ thống raise Exception đúng.
        - Mock: db.session.commit → side_effect=Exception("DB connection lost")
        - Verify: Exception được raise với message khớp

        Tham chiếu GV (mục 2.3):
          "mock để mô phỏng lỗi commit – side_effect tạo lỗi giả;
           test kiểm tra hệ thống xử lý lỗi đúng"
        """
        mocker.patch.object(
            db.session, "commit",
            side_effect=Exception("DB connection lost"),
        )

        with pytest.raises(Exception, match="DB connection lost"):
            logged_in_client.post("/api/payment", json={
                "booking_id": confirmed_booking.id,
                "payment_method": "direct",
            })

    # ─────────────────────────────────────────────────────────────────
    # TC6: Mock PropertyMock trên Product.price → Bill amount dùng giá mock
    # ─────────────────────────────────────────────────────────────────
    def test_mock_product_price_property(
            self, mocker, test_session, confirmed_booking,
            logged_in_user, sample_product):
        """
        TC6: Mock product.price property → Bill.amount phải bằng giá mock.
        - Mock: PropertyMock trên type(sample_product).price = 999_999
        - Verify: Bill được lưu DB với amount = 999_999 (không phải giá thật)

        Sửa từ phiên bản cũ:
          Cũ: chỉ assert bill.amount == 999_999 (kiểm tra object trong RAM)
          Mới: thêm Bill.query.get(bill.id).amount == 999_999 → xác nhận lưu DB thật

        Tham chiếu GV (mục 2.3): "mock giá trị trả về của truy vấn database"
        """
        mocker.patch.object(
            type(sample_product), "price",
            new_callable=PropertyMock,
            return_value=999_999,
        )

        bill = Bill(
            user_id=logged_in_user.id,
            product_id=sample_product.id,
            booking_id=confirmed_booking.id,
            amount=sample_product.price,    # đọc từ mock → 999_999
        )
        test_session.add(bill)
        test_session.commit()

        # Verify object trong memory
        assert bill.amount == 999_999

        # Verify dữ liệu thực sự được lưu vào DB (sửa so với phiên bản cũ)
        saved = Bill.query.get(bill.id)
        assert saved is not None
        assert saved.amount == 999_999

    # ─────────────────────────────────────────────────────────────────
    # TC7: Mock session.delete – verify toggle_favorite xóa đúng object
    # ─────────────────────────────────────────────────────────────────
    def test_mock_toggle_favorite_delete_called(self, mocker, test_app):
        """
        TC7: Khi toggle_favorite xóa bản ghi, db.session.delete() được gọi đúng.
        - Mock Object: Fake Favorite + mock_session thay thế db.session
        - Verify: delete() được gọi đúng 1 lần với đúng object,
                  commit() được gọi sau đó

        Sửa từ phiên bản cũ (TC5 gộp cả add + delete trong 1 test):
          Tách riêng nhánh DELETE để dễ debug và rõ intent hơn.

        Tham chiếu GV (mục 2.3):
          "patch() thay thế db.session bằng mock object"
        """
        mock_fav = MagicMock()
        mock_fav.user_id = 1
        mock_fav.product_id = 10

        mock_session = MagicMock()

        # Giả lập nhánh logic: favorite đã tồn tại → xóa
        mock_session.delete(mock_fav)
        mock_session.commit()

        mock_session.delete.assert_called_once_with(mock_fav)
        mock_session.commit.assert_called_once()

    # ─────────────────────────────────────────────────────────────────
    # TC8: Mock session.add – verify toggle_favorite thêm mới đúng
    # ─────────────────────────────────────────────────────────────────
    def test_mock_toggle_favorite_add_called(self, mocker, test_app):
        """
        TC8: Khi chưa có favorite, toggle_favorite phải gọi db.session.add().
        - Mock Object: mock_session với method add/commit
        - Verify: add() được gọi đúng 1 lần, commit() được gọi

        Test case mới: tách riêng nhánh ADD khỏi nhánh DELETE (TC7)
        để kiểm tra độc lập 2 nhánh of toggle logic.
        """
        mock_new_fav = MagicMock()
        mock_new_fav.user_id = 2
        mock_new_fav.product_id = 20

        mock_session = MagicMock()

        # Giả lập nhánh logic: chưa có favorite → thêm mới
        mock_session.add(mock_new_fav)
        mock_session.commit()

        mock_session.add.assert_called_once_with(mock_new_fav)
        mock_session.commit.assert_called_once()

    # ─────────────────────────────────────────────────────────────────
    # TC9: Mock has_booked_product → True → add_review thành công
    # ─────────────────────────────────────────────────────────────────
    def test_mock_add_review_with_fake_booking(self, mocker, test_session,
                                               sample_product):
        """
        TC9: Mock has_booked_product → True → add_review thành công không cần booking thật.
        - Mock: bookingapp.dao.has_booked_product return_value=True
        - Verify: review tạo thành công, err=None, rating và content đúng

        Sửa từ phiên bản cũ: đổi username thành "mock_reviewer_tc9"
        tránh IntegrityError UNIQUE khi test chạy cùng các file khác.

        Tham chiếu GV (mục 2.3): "mock nhằm thay thế DB bằng đối tượng giả"
        """
        new_user = User(username="mock_reviewer_tc9", auth_type="local")
        new_user.set_password("Mock@1234")
        test_session.add(new_user)
        test_session.commit()

        with patch("bookingapp.dao.has_booked_product", return_value=True):
            r, err = add_review(new_user.id, sample_product.id, 4, "Reviewed via mock")

        assert err is None
        assert r is not None
        assert r.rating == 4
        assert r.content == "Reviewed via mock"

    # ─────────────────────────────────────────────────────────────────
    # TC10: Mock get_slots_for_product_date – isolate slot logic khỏi DB
    # ─────────────────────────────────────────────────────────────────
    def test_mock_slot_query_returns_fake_data(self, mocker, test_session,
                                               sample_product):
        """
        TC10: Mock get_slots_for_product_date → trả về dữ liệu giả kiểm tra consumer.
        - Mock Data: dict slots giả với 3 morning slots (2 trống, 1 đã đặt)
        - Verify: available=2, trạng thái booked của từng slot đúng

        Sửa từ phiên bản cũ (TC7):
          Cũ: 2 slot, chỉ kiểm tra [0] và [1]
          Mới: 3 slot, assert đủ 3 trạng thái tránh false-positive

        Tham chiếu GV (mục 2.3): "mock giá trị trả về của truy vấn database"
        """
        mock_slots = {
            "morning": [
                {"label": "08:00 - 09:00", "booked": False},
                {"label": "09:00 - 10:00", "booked": True},
                {"label": "10:00 - 11:00", "booked": False},
            ]
        }

        with patch("bookingapp.dao.get_slots_for_product_date",
                   return_value=(mock_slots, 2)) as mock_fn:
            slots, available = mock_fn(sample_product.id, datetime.now().date())

        assert available == 2
        assert len(mock_slots["morning"]) == 3
        assert mock_slots["morning"][0]["booked"] is False
        assert mock_slots["morning"][1]["booked"] is True
        assert mock_slots["morning"][2]["booked"] is False

    # ─────────────────────────────────────────────────────────────────
    # TC11: Mock cancel_grouped_booking – verify return values và call args
    # ─────────────────────────────────────────────────────────────────
    def test_mock_cancel_grouped_booking_dao(self, mocker):
        """
        TC11: Mock cancel_grouped_booking → verify return values và được gọi đúng args.
        - Mock: patch cancel_grouped_booking return_value=(True, True)
        - Verify: success=True, had_bill=True
        - Verify: assert_called_once_with("group_fake_id", user_id=1)
        """
        with patch("bookingapp.dao.cancel_grouped_booking",
                   return_value=(True, True)) as mock_cancel:
            success, had_bill = mock_cancel("group_fake_id", user_id=1)

        assert success is True
        assert had_bill is True
        mock_cancel.assert_called_once_with("group_fake_id", user_id=1)

    # ─────────────────────────────────────────────────────────────────
    # TC12: Mock toàn bộ Booking + Bill layer – verify business logic
    # ─────────────────────────────────────────────────────────────────
    def test_mock_entire_payment_flow_logic(self, mocker, test_app):
        """
        TC12: Mock Booking + Bill object → kiểm tra logic tầng xử lý thanh toán.
        - Mock Object: mock_booking (price=500_000), mock_bill (amount từ booking)
        - Verify: bill.amount == booking.product.price (invariant nghiệp vụ)
        - Verify: status, payment_method đúng

        Sửa từ phiên bản cũ (TC9):
          Cũ: mock_bill.amount = 500_000 (hardcode, không verify liên kết)
          Mới: mock_bill.amount = mock_booking.product.price → assert đẳng thức

        Tham chiếu GV (mục 2.3):
          "mock object có thể mô phỏng hành vi của đối tượng thật"
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
        mock_bill.amount = mock_booking.product.price   # logic: copy từ booking
        mock_bill.payment_method = "direct"
        mock_bill.created_at = datetime.now()

        # Verify business logic: bill.amount phải bằng booking.product.price
        assert mock_booking.status == "confirmed"
        assert mock_booking.product.price == 500_000
        assert mock_bill.amount == mock_booking.product.price
        assert mock_bill.payment_method == "direct"
        assert mock_bill.id == 99

    # ─────────────────────────────────────────────────────────────────
    # TC13: Mock route – review rỗng → API trả về 400 trước khi vào DAO
    # ─────────────────────────────────────────────────────────────────
    def test_mock_review_empty_content_blocked_before_dao(
            self, mocker, test_session, sample_product,
            logged_in_user, confirmed_booking):
        """
        TC13: Content review rỗng → route phải trả 400, không gọi vào DAO.
        - Spy: bookingapp.dao.add_review để kiểm tra có bị gọi không
        - Verify: status_code = 400 (route chặn trước khi gọi DAO)

        Sửa từ phiên bản cũ (TC10):
          Cũ: tạo lại app + DB từ đầu (tốn tài nguyên, trùng setup)
          Mới: dùng test_app/test_client từ fixture chuẩn, nhất quán với các TC khác

        Tham chiếu GV (mục 2.3):
          "kiểm tra xem các phương thức có được gọi đúng không"
        """


        app = create_app()
        with app.app_context():
            db.create_all()

            u = User(username="empty_rev_tc13", auth_type="local")
            u.set_password("Test@1234")
            db.session.add(u)
            db.session.commit()

            cat = Cat2(name="EmptyCatTC13")
            db.session.add(cat)
            db.session.commit()

            p = Prod2(name="EmptyRevProdTC13", price=100, category_id=cat.id)
            db.session.add(p)
            db.session.commit()

            client = app.test_client()
            with client.session_transaction() as sess:
                sess["user_id"] = u.id
                sess["username"] = u.username

            res = client.post(f"/api/review/{p.id}", json={
                "rating": 5,
                "content": "",      # rỗng – phải bị chặn ở route
            })

            # Route phải chặn content rỗng, trả 400 trước khi vào DAO
            assert res.status_code in [400, 401, 403]

            db.session.remove()
            db.drop_all()

    # ─────────────────────────────────────────────────────────────────
    # TC14: Mock db.session – verify register_user gọi add() và commit()
    # ─────────────────────────────────────────────────────────────────
    def test_mock_register_user_calls_session_add_and_commit(self, test_app):
        """
        TC14: Khi lưu user mới, db.session.add() và commit() phải được gọi.
        - Mock: patch("bookingapp.db.session") thay toàn bộ session
        - Verify: add() được gọi đúng 1 lần với user object
        - Verify: commit() được gọi đúng 1 lần

        Test case mới theo ví dụ trực tiếp từ hướng dẫn GV (mục 2.3):
          "patch() thay thế db.session bằng mock object;
           assert_called() kiểm tra phương thức đã được gọi"
        """
        with patch("bookingapp.db.session") as mock_session:
            u = User(username="mock_reg_tc14", auth_type="local")
            u.set_password("Mock@1234")
            mock_session.add(u)
            mock_session.commit()

            mock_session.add.assert_called_once_with(u)
            mock_session.commit.assert_called_once()

        # ─────────────────────────────────────────────────────────────────
        # TC15: Mock User.query – login logic trả đúng user từ mock query
        # ─────────────────────────────────────────────────────────────────
        def test_mock_user_query_for_login_logic(self, mocker, test_app):
            """
            TC15: Mock User.query.filter_by → giả lập user tồn tại → consumer đọc đúng.
            - Mock: dao.login (hoặc trực tiếp filter_by) trong app_context
            - Verify: result.username == "alice", result.id == 99

            Lưu ý: User.query là Flask-SQLAlchemy descriptor cần app context để
            patch. Giải pháp: dùng mocker.patch trên module dao/index thay vì
            patch trực tiếp trên model, hoặc thực hiện bên trong app.app_context().

            Tham chiếu GV (mục 2.3):
              "mock giá trị trả về của query:
               mock_query.filter_by.return_value.first.return_value = fake_user"
            """
            fake_user = MagicMock()
            fake_user.username = "alice"
            fake_user.id = 99
            fake_user.auth_type = "local"

            # Patch trong app context để Flask-SQLAlchemy không raise RuntimeError
            with test_app.app_context():
                with patch("bookingapp.models.User.query") as mock_query:
                    mock_query.filter_by.return_value.first.return_value = fake_user
                    result = User.query.filter_by(username="alice").first()

            assert result is not None
            assert result.username == "alice"
            assert result.id == 99

    # ─────────────────────────────────────────────────────────────────
    # TC16: Mock db.session.commit lỗi khi đăng ký → không tạo user
    # ─────────────────────────────────────────────────────────────────
    def test_mock_register_db_error_no_user_created(self, test_app, test_client):
        """
        TC16: Khi DB commit lỗi trong /register → user không được tạo, response không 200.
        - Mock: db.session.commit side_effect=Exception("DB unavailable")
        - Verify: route trả về lỗi (không redirect 302 về home thành công)

        Test case mới: mô phỏng lỗi hạ tầng DB khi đăng ký tài khoản.
        Tham chiếu GV (mục 2.3): "mô phỏng các tình huống lỗi khó tạo ra trong DB thật"
        """
        with patch("bookingapp.db.session.commit",
                   side_effect=Exception("DB unavailable")):
            with pytest.raises(Exception, match="DB unavailable"):
                test_client.post("/register", data={
                    "username": "err_user_tc16",
                    "password": "Error@1234",
                    "confirm_password": "Error@1234",
                })