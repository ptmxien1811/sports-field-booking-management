
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import render_template, session, redirect, url_for, request, flash, jsonify
from bookingapp import app, db
from bookingapp.dao import (get_bookings_by_user, get_favorites_by_user,
                             get_slots_for_product_date, create_booking,
                             cancel_booking_by_id, toggle_favorite,
                             add_review, get_product_by_id,
                             has_booked_product, has_reviewed_product,
                             get_grouped_bookings_by_user, cancel_grouped_booking)
from bookingapp.models import Product, User, Booking, Bill, Favorite, Review
from bookingapp import admin
from datetime import datetime, timedelta, date as date_type
import datetime as dt
import requests as http_requests
import os
from sqlalchemy import func
import uuid

# ===== CẤU HÌNH GOOGLE OAUTH =====
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID",     "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI",  "http://localhost:5000/auth/google/callback")

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"

def register_routes(app):
    # if "home" in app.view_functions:
    #     app.view_functions.pop("home")
    # ===== HOME =====
    @app.route("/")
    def home():
        products     = Product.query.filter_by(active=True).all()
        user_id      = session.get("user_id")
        username     = session.get("username")
        grouped_bookings = []
        favorites    = []
        favorite_ids = []
        paid_group_keys = []
        if user_id:
            grouped_bookings = get_grouped_bookings_by_user(user_id)
            favorites    = get_favorites_by_user(user_id)
            favorite_ids = [f.product_id for f in favorites]
            # Tìm những nhóm booking đã thanh toán (đã có Bill)
            for g in grouped_bookings:
                paid_bills = Bill.query.filter(Bill.booking_id.in_(g["booking_ids"])).all()
                if paid_bills:
                    key = g["group_id"] if g["group_id"] else str(g["booking_ids"][0])
                    paid_group_keys.append(key)

        return render_template("index.html",
                               products=products,
                               grouped_bookings=grouped_bookings,
                               paid_group_keys=paid_group_keys,
                               favorites=favorites,
                               favorite_ids=favorite_ids,
                               username=username)


    # ===== AUTH: ĐĂNG NHẬP THƯỜNG =====
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["user_id"] = user.id
                session["username"] = user.username
                if username.lower() == "admin":
                    return redirect("/admin")
                # Xử lý next param
                next_url = request.args.get("next") or request.form.get("next")
                return redirect(next_url if next_url else url_for("home"))
        return render_template("login.html", error="Tên đăng nhập hoặc mật khẩu không đúng!")


    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))


    # ===== AUTH: ĐĂNG KÝ THƯỜNG =====
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm  = request.form.get("confirm_password", "")
            email    = request.form.get("email", "").strip() or None
            phone    = request.form.get("phone", "").strip() or None

            if not username:
                return render_template("register.html", error="Vui lòng nhập tên đăng nhập")
            ok, msg = User.validate_password(password)
            if not ok:
                return render_template("register.html", error=msg)
            if password != confirm:
                return render_template("register.html", error="Mật khẩu xác nhận không khớp")
            if User.query.filter_by(username=username).first():
                return render_template("register.html", error="Tên đăng nhập đã tồn tại")
            if email:
                if not User.validate_email(email):
                    return render_template("register.html", error="Email không hợp lệ")
                if User.query.filter_by(email=email).first():
                    return render_template("register.html", error="Email này đã được sử dụng")
            if phone:
                if not User.validate_phone(phone):
                    return render_template("register.html", error="Số điện thoại không hợp lệ (cần 10 số, bắt đầu 0)")
                if User.query.filter_by(phone=phone).first():
                    return render_template("register.html", error="Số điện thoại này đã được sử dụng")

            user = User(username=username, password="", email=email, phone=phone, auth_type='local')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session["user_id"]  = user.id
            session["username"] = user.username
            return redirect(url_for("home"))

        return render_template("register.html")


    # ===== AUTH: ĐĂNG NHẬP BẰNG EMAIL =====
    @app.route("/login/email", methods=["GET", "POST"])
    def login_email():
        if request.method == "POST":
            email    = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            if not User.validate_email(email):
                return render_template("login.html", error="Email không hợp lệ")
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                return render_template("login.html", error="Email hoặc mật khẩu không đúng")
            session["user_id"]  = user.id
            session["username"] = user.username
            return redirect(url_for("home"))
        return render_template("login.html")


    # ===== AUTH: ĐĂNG KÝ BẰNG EMAIL =====
    @app.route("/register/email", methods=["GET", "POST"])
    def register_email():
        if request.method == "POST":
            email    = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            confirm  = request.form.get("confirm_password", "")
            username = request.form.get("username", "").strip()

            if not User.validate_email(email):
                return render_template("register.html", error="Email không hợp lệ")
            if User.query.filter_by(email=email).first():
                return render_template("register.html", error="Email này đã được sử dụng")
            ok, msg = User.validate_password(password)
            if not ok:
                return render_template("register.html", error=msg)
            if password != confirm:
                return render_template("register.html", error="Mật khẩu xác nhận không khớp")
            if not username:
                username = email.split("@")[0]
            base = username; i = 1
            while User.query.filter_by(username=username).first():
                username = f"{base}{i}"; i += 1

            user = User(username=username, email=email, password="", auth_type='email')
            user.set_password(password)
            db.session.add(user); db.session.commit()
            return redirect(url_for("home"))
        return render_template("register.html")


    # ===== AUTH: ĐĂNG NHẬP BẰNG SĐT =====
    @app.route("/login/phone", methods=["GET", "POST"])
    def login_phone():
        if request.method == "POST":
            phone    = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            if not User.validate_phone(phone):
                flash("Số điện thoại không hợp lệ", "danger")   # ← dùng flash
                return render_template("login.html")
            user = User.query.filter_by(phone=phone).first()
            if not user or not user.check_password(password):
                flash("Số điện thoại hoặc mật khẩu không đúng", "danger")
                return render_template("login.html")
            session["user_id"]  = user.id
            session["username"] = user.username
            return redirect(url_for("home"))
        return render_template("login.html")


    # ===== AUTH: ĐĂNG KÝ BẰNG SĐT =====
    @app.route("/register/phone", methods=["GET", "POST"])
    def register_phone():
        if request.method == "POST":
            phone    = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            confirm  = request.form.get("confirm_password", "")
            username = request.form.get("username", "").strip()

            if not User.validate_phone(phone):
                return render_template("register.html", error="Số điện thoại không hợp lệ (10 số, bắt đầu 0)")
            if User.query.filter_by(phone=phone).first():
                return render_template("register.html", error="Số điện thoại này đã được sử dụng")
            ok, msg = User.validate_password(password)
            if not ok:
                return render_template("register.html", error=msg)
            if password != confirm:
                return render_template("register.html", error="Mật khẩu xác nhận không khớp")
            if not username:
                username = f"user_{phone[-4:]}"
            base = username; i = 1
            while User.query.filter_by(username=username).first():
                username = f"{base}{i}"; i += 1

            user = User(username=username, phone=phone, password="", auth_type='phone')
            user.set_password(password)
            db.session.add(user); db.session.commit()
            return redirect(url_for("home"))
        return render_template("register.html")


    # ===== GOOGLE OAUTH =====
    @app.route("/auth/google")
    def google_login():
        import urllib.parse
        params = {
            "client_id":     GOOGLE_CLIENT_ID,
            "redirect_uri":  GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope":         "openid email profile",
            "access_type":   "offline",
        }
        url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
        return redirect(url)


    @app.route("/auth/google/callback")
    def google_callback():
        code = request.args.get("code")
        if not code:
            return redirect(url_for("login"))

        token_res = http_requests.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        })
        token_data   = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return redirect(url_for("login"))

        user_res  = http_requests.get(GOOGLE_USER_URL, headers={"Authorization": f"Bearer {access_token}"})
        user_info = user_res.json()

        google_id    = user_info.get("sub")
        google_email = user_info.get("email")
        google_name  = user_info.get("name", "")

        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=google_email).first()
            if user:
                user.google_id = google_id; user.google_email = google_email
                db.session.commit()
            else:
                username = google_name.replace(" ", "") or f"user_{google_id[:6]}"
                base = username; i = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base}{i}"; i += 1
                user = User(username=username, email=google_email, google_id=google_id,
                            google_email=google_email, auth_type='google', password="")
                db.session.add(user); db.session.commit()

        session["user_id"]  = user.id
        session["username"] = user.username
        return redirect(url_for("home"))


    # ===== VENUE DETAIL =====
    @app.route("/venue/<int:id>")
    def venue_detail(id):
        product      = get_product_by_id(id)
        user_id      = session.get("user_id")
        can_review   = False
        has_reviewed = False
        if user_id:
            can_review   = has_booked_product(user_id, id)
            has_reviewed = has_reviewed_product(user_id, id)
        return render_template(
            "venue_detail.html",
            product      = product,
            username     = session.get("username"),
            can_review   = can_review,
            has_reviewed = has_reviewed,
        )


    # ===== API: LẤY SLOTS =====
    @app.route("/api/slots/<int:product_id>")
    def api_slots(product_id):
        date_str = request.args.get("date", "")
        try:
            sel_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            sel_date = date_type.today()

        user_id       = session.get("user_id")
        # SAU (ĐÚNG)
        bookings_today = 0
        if user_id:
            day_start = datetime.combine(sel_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)
            # Đếm số SÂN KHÁC NHAU đã đặt trong ngày
            booked_product_ids = db.session.query(Booking.product_id).filter(
                Booking.user_id == user_id,
                Booking.date >= day_start,
                Booking.date < day_end,
                Booking.status == "confirmed"
            ).distinct().all()
            bookings_today = len(booked_product_ids)
        slots_data, available = get_slots_for_product_date(product_id, sel_date)
        return jsonify({
            "slots":          slots_data,
            "available":      available,
            "bookings_today": bookings_today,
            "max_per_day":    3,
        })


    # ===== API: ĐẶT SÂN (NHIỀU KHUNG GIỜ) =====
    @app.route("/api/book", methods=["POST"])
    def api_book():
        if not session.get("user_id"):
            return jsonify({"ok": False, "msg": "Vui lòng đăng nhập để đặt sân"}), 401

        data       = request.json
        product_id = data.get("product_id")
        date_str   = data.get("date")

        # Hỗ trợ cả 1 slot (string) và nhiều slots (list)
        slots_raw = data.get("slots") or data.get("slot")
        if isinstance(slots_raw, str):
            slot_labels = [slots_raw]
        elif isinstance(slots_raw, list):
            slot_labels = slots_raw
        else:
            slot_labels = []

        if not slot_labels:
            return jsonify({"ok": False, "msg": "Vui lòng chọn ít nhất 1 khung giờ"}), 400

        try:
            sel_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"ok": False, "msg": "Ngày không hợp lệ"}), 400

        booked_ids = []
        errors     = []

        # Tạo group_id nếu đặt nhiều khung giờ
        grp_id = str(uuid.uuid4())[:8] if len(slot_labels) > 1 else None

        for slot_label in slot_labels:
            b, err = create_booking(session["user_id"], product_id, slot_label, sel_date)
            if err:
                errors.append(f"{slot_label}: {err}")
            else:
                if grp_id:
                    b.group_id = grp_id
                booked_ids.append(b.id)

        # Nếu đặt nhiều slot nhưng chỉ 1 thành công → xoá group_id
        if grp_id and len(booked_ids) == 1:
            booking_obj = db.session.get(Booking, booked_ids[0])
            if booking_obj:
                booking_obj.group_id = None

        if booked_ids:
            db.session.commit()

        if not booked_ids:
            return jsonify({"ok": False, "msg": "; ".join(errors)}), 400

        msg = f"Đặt thành công {len(booked_ids)} khung giờ!"
        if errors:
            msg += f" ({len(errors)} khung giờ thất bại)"

        return jsonify({"ok": True, "booking_ids": booked_ids, "msg": msg})


    # ===== API: TOGGLE FAVORITE =====
    @app.route("/api/favorite/<int:product_id>", methods=["POST"])
    def api_favorite(product_id):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "msg": "Chưa đăng nhập"}), 401

        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"ok": False, "msg": "Sân không tồn tại"}), 404

        added = toggle_favorite(user_id, product_id)
        return jsonify({"ok": True, "added": added})

    # ===== API: GỬI ĐÁNH GIÁ =====
    @app.route("/api/review/<int:product_id>", methods=["POST"])
    def api_review(product_id):
        if not session.get("user_id"):
            return jsonify({"ok": False, "msg": "Vui lòng đăng nhập để đánh giá"}), 401

        data    = request.json
        rating  = int(data.get("rating", 5))
        content = data.get("content", "").strip()

        if not content:
            return jsonify({"ok": False, "msg": "Vui lòng nhập nội dung đánh giá"}), 400

        r, err = add_review(session["user_id"], product_id, rating, content)
        if err:
            return jsonify({"ok": False, "msg": err}), 403

        return jsonify({
            "ok":      True,
            "author":  session["username"],
            "rating":  r.rating,
            "stars":   r.stars,
            "content": r.content,
            "date_str": r.date_str,
        })


    # ===== API: KIỂM TRA QUYỀN REVIEW =====
    @app.route("/api/can-review/<int:product_id>")
    def api_can_review(product_id):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"can_review": False, "has_reviewed": False, "reason": "not_logged_in"})
        booked   = has_booked_product(user_id, product_id)
        reviewed = has_reviewed_product(user_id, product_id)
        return jsonify({
            "can_review":   booked and not reviewed,
            "has_reviewed": reviewed,
            "has_booked":   booked,
            "reason": "ok" if (booked and not reviewed) else ("already_reviewed" if reviewed else "not_booked")
        })


    # ===== CANCEL BOOKING =====
    @app.route("/api/cancel-booking/<int:id>", methods=["POST"])
    @app.route("/api/cancel-booking/<int:id>", methods=["POST"])
    def cancel_booking_final(id):
        user_id = session.get("user_id")

        # Kiểm tra có Bill (đã thanh toán) trước khi hủy
        had_bill = Bill.query.filter_by(booking_id=id).first() is not None

        success = cancel_booking_by_id(id, user_id)

        if success:
            db.session.commit()
            if had_bill:
                flash("Đã hoàn tiền và hủy sân thành công!", "success")
            else:
                flash("Đã hủy thành công!", "success")

        else:
            flash("Không thể hủy! (Sai user, quá giờ hoặc đang sử dụng)", "danger")

        return redirect(url_for("home", _anchor="booked"))


    # ===== CANCEL GROUPED BOOKING =====
    @app.route("/api/cancel-group/<group_id>", methods=["POST"])
    def cancel_group_booking(group_id):
        user_id = session.get("user_id")
        success, had_bill = cancel_grouped_booking(group_id, user_id)

        if success:
            if had_bill:
                flash("Đã hoàn tiền và hủy sân thành công!", "success")
            else:
                flash("Đã hủy thành công!", "success")
        else:
            flash("Không thể hủy! (Sân sắp sử dụng, đang sử dụng hoặc đã sử dụng xong)", "danger")

        return redirect(url_for("home", _anchor="booked"))


    # ===== ACCOUNT PAGE =====
    @app.route("/account")
    def account():
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return render_template("account.html", username=session.get("username"))


    # ===== API: ACCOUNT - STATS =====
    @app.route("/api/my-bookings")
    def api_my_bookings():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False}), 401
        count = Booking.query.filter_by(user_id=user_id, status="confirmed").count()
        return jsonify({"bookings": count})


    @app.route("/api/my-favorites")
    def api_my_favorites():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False}), 401
        count = Favorite.query.filter_by(user_id=user_id).count()
        return jsonify({"favorites": count})


    @app.route("/api/my-reviews")
    def api_my_reviews():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False}), 401
        count = Review.query.filter_by(user_id=user_id).count()
        return jsonify({"reviews": count})


    # ===== API: ACCOUNT - BOOKING HISTORY (detail) =====
    @app.route("/api/my-bookings-detail")
    def api_my_bookings_detail():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False}), 401

        bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.date.desc()).all()
        items = []
        for b in bookings:
            items.append({
                "id":           b.id,
                "product_name": b.product.name,
                "image":        b.product.image,
                "address":      b.product.address or "",
                "price":        b.product.price,
                "slot_label":   b.slot_label,
                "date_str":     b.date.strftime("%d/%m/%Y") if b.date else "",
                "status":       b.status,
            })
        return jsonify({"items": items})


    # ===== API: ACCOUNT - FAVORITES (detail) =====
    @app.route("/api/my-favorites-detail")
    def api_my_favorites_detail():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False}), 401

        favs = Favorite.query.filter_by(user_id=user_id).all()
        items = []
        for f in favs:
            items.append({
                "product_id":   f.product.id,
                "product_name": f.product.name,
                "image":        f.product.image,
                "price":        f.product.price,
            })
        return jsonify({"items": items})


    # ===== API: UPDATE PROFILE =====
    @app.route("/api/update-profile", methods=["POST"])
    def api_update_profile():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "msg": "Chưa đăng nhập"}), 401

        user  = db.session.get(User, user_id)
        data  = request.json
        email = data.get("email", "").strip() or None
        phone = data.get("phone", "").strip() or None

        if email:
            if not User.validate_email(email):
                return jsonify({"ok": False, "msg": "Email không hợp lệ"})
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user_id:
                return jsonify({"ok": False, "msg": "Email này đã được sử dụng"})
            user.email = email

        if phone:
            if not User.validate_phone(phone):
                return jsonify({"ok": False, "msg": "Số điện thoại không hợp lệ"})
            existing = User.query.filter_by(phone=phone).first()
            if existing and existing.id != user_id:
                return jsonify({"ok": False, "msg": "Số điện thoại này đã được sử dụng"})
            user.phone = phone

        db.session.commit()
        return jsonify({"ok": True})


    # ===== API: CHANGE PASSWORD =====
    @app.route("/api/change-password", methods=["POST"])
    def api_change_password():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "msg": "Chưa đăng nhập"}), 401

        user    = db.session.get(User, user_id)
        data    = request.json
        current = data.get("current_password", "")
        new_pw  = data.get("new_password", "")

        if not user.check_password(current):
            return jsonify({"ok": False, "msg": "Mật khẩu hiện tại không đúng"})

        ok, msg = User.validate_password(new_pw)
        if not ok:
            return jsonify({"ok": False, "msg": msg})

        user.set_password(new_pw)
        db.session.commit()
        return jsonify({"ok": True})


    # ===== TRANG THANH TOÁN =====
    @app.route("/payment/<int:booking_id>")
    def payment_page(booking_id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Vui lòng đăng nhập để thanh toán", "danger")
            return redirect(url_for("login"))

        booking = Booking.query.get(booking_id)
        if not booking or booking.user_id != user_id:
            flash("Không tìm thấy đơn đặt sân", "danger")
            return redirect(url_for("home"))

        # Kiểm tra đã thanh toán chưa
        existing_bill = Bill.query.filter_by(booking_id=booking_id).first()
        is_paid = existing_bill is not None

        user = db.session.get(User, user_id)
        product = booking.product

        # Nếu booking thuộc group → lấy tất cả slot + tính tổng tiền
        group_bookings = []
        total_amount = product.price
        if booking.group_id:
            group_bookings = Booking.query.filter_by(
                group_id=booking.group_id, status="confirmed"
            ).order_by(Booking.start_time).all()
            total_amount = product.price * len(group_bookings)
            # Kiểm tra bill qua tất cả booking trong nhóm
            if not is_paid:
                g_ids = [gb.id for gb in group_bookings]
                existing_bill = Bill.query.filter(Bill.booking_id.in_(g_ids)).first()
                is_paid = existing_bill is not None

        return render_template("payment.html",
                               booking=booking,
                               group_bookings=group_bookings,
                               total_amount=total_amount,
                               user=user,
                               product=product,
                               username=session.get("username"),
                               is_paid=is_paid,
                               bill=existing_bill)


    # ===== API: XỬ LÝ THANH TOÁN =====
    @app.route("/api/payment", methods=["POST"])
    def api_payment():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "msg": "Chưa đăng nhập"}), 401

        data = request.json
        booking_id     = data.get("booking_id")
        payment_method = data.get("payment_method", "direct")
        db.session.expire_all()
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return jsonify({"ok": False, "msg": "Không tìm thấy đơn đặt sân"}), 404
        if booking.user_id != user_id:
            return jsonify({"ok": False, "msg": "Bạn không có quyền thanh toán đơn này"}), 403
        # Tính tổng tiền: nếu thuộc group → nhân theo số slot
        if booking.group_id:
            group_bookings = Booking.query.filter_by(
                group_id=booking.group_id, status="confirmed"
            ).all()
            # Kiểm tra đã thanh toán chưa (bất kỳ booking nào trong nhóm)
            g_ids = [gb.id for gb in group_bookings]
            existing_bill = Bill.query.filter(Bill.booking_id.in_(g_ids)).first()
            if existing_bill:
                return jsonify({"ok": False, "msg": f"Đã thanh toán rồi! Mã hóa đơn: #{existing_bill.id}"}), 400
            total_amount = booking.product.price * len(group_bookings)
        else:
            # Đặt lẻ: kiểm tra bình thường
            existing_bill = Bill.query.filter_by(booking_id=booking_id).first()
            if existing_bill:
                return jsonify({"ok": False, "msg": f"Đã thanh toán rồi! Mã hóa đơn: #{existing_bill.id}"}), 400
            total_amount = booking.product.price

        # Tạo hóa đơn mới
        bill = Bill(
            user_id=user_id,
            product_id=booking.product_id,
            booking_id=booking.id,
            amount=total_amount,
            payment_method=payment_method
        )
        db.session.add(bill)
        db.session.commit()

        return jsonify({
            "ok": True,
            "msg": f"Thanh toán thành công! Mã hóa đơn của bạn là #{bill.id}",
            "bill_id": bill.id
        })


    @app.route("/stats")
    def stats():
        # ===== KIỂM TRA QUYỀN: Chỉ admin mới vào được =====
        if not (session.get("username") and session.get("username").lower() == "admin"):
            flash("Bạn không có quyền truy cập!", "danger")
            return redirect(url_for("login"))

        start_date = request.args.get("start_date")
        end_date   = request.args.get("end_date")
        today = datetime.now().date()

        start = None
        end   = None

        # ===== XỬ LÝ START DATE =====
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                if start_dt > today: start_dt = today
                start = datetime.combine(start_dt, datetime.min.time())
            except: pass

        # ===== XỬ LÝ END DATE =====
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                if end_dt > today: end_dt = today
                end = datetime.combine(end_dt, datetime.min.time()) + timedelta(days=1)
            except: pass

        # ===== RÀNG BUỘC: Ngày bắt đầu phải <= Ngày kết thúc =====
        if start and end and start >= end:
            # Nếu lỡ nhập ngược, ta đảo lại cho admin luôn
            start, end = datetime.combine(end_dt, datetime.min.time()), datetime.combine(start_dt, datetime.min.time()) + timedelta(days=1)
            start_date, end_date = end_date, start_date




        # ===== QUERY TỔNG =====
        query = db.session.query(Bill)

        if start:
            query = query.filter(Bill.created_at >= start)

        if end:
            query = query.filter(Bill.created_at < end)

        bills = query.all()

        total_revenue = sum(b.amount for b in bills)
        total_bookings = len(bills)

        # ===== DOANH THU THEO LOẠI SÂN (CATEGORY) =====
        from bookingapp.models import Category
        cat_query = db.session.query(
            Category.name,
            func.sum(Bill.amount)
        ).join(Product, Product.id == Bill.product_id) \
         .join(Category, Category.id == Product.category_id)

        if start:
            cat_query = cat_query.filter(Bill.created_at >= start)
        if end:
            cat_query = cat_query.filter(Bill.created_at < end)

        cat_revenue = cat_query.group_by(Category.name).all()

        # Tính phần trăm theo từng loại sân
        category_stats = []
        for cat_name, cat_total in cat_revenue:
            pct = round((cat_total / total_revenue * 100), 1) if total_revenue > 0 else 0
            category_stats.append({
                'name': cat_name,
                'revenue': cat_total,
                'percent': pct
            })

        cat_labels = [c['name'] for c in category_stats]
        cat_values = [c['revenue'] for c in category_stats]

        # ===== SO SÁNH VỚI THÁNG TRƯỚC =====
        first_of_this_month = today.replace(day=1)
        last_month_end = first_of_this_month - timedelta(days=1)
        first_of_last_month = last_month_end.replace(day=1)

        # Doanh thu tháng này (tính đến hôm nay)
        this_month_rev = db.session.query(func.sum(Bill.amount)).filter(
            Bill.created_at >= datetime.combine(first_of_this_month, datetime.min.time()),
            Bill.created_at <= datetime.combine(today, datetime.min.time()) + timedelta(days=1)
        ).scalar() or 0

        # Doanh thu tháng trước (toàn bộ tháng)
        last_month_rev = db.session.query(func.sum(Bill.amount)).filter(
            Bill.created_at >= datetime.combine(first_of_last_month, datetime.min.time()),
            Bill.created_at < datetime.combine(first_of_this_month, datetime.min.time())
        ).scalar() or 0

        # Tính % thay đổi
        if last_month_rev > 0:
            growth_pct = round(((this_month_rev - last_month_rev) / last_month_rev) * 100, 1)
        else:
            growth_pct = 100.0 if this_month_rev > 0 else 0.0

        # ===== CHART DOANH THU THEO NGÀY =====
        revenue_query = db.session.query(
            func.date(Bill.created_at),
            func.sum(Bill.amount)
        )

        if start:
            revenue_query = revenue_query.filter(Bill.created_at >= start)

        if end:
            revenue_query = revenue_query.filter(Bill.created_at < end)

        revenue_by_day = revenue_query \
            .group_by(func.date(Bill.created_at)) \
            .order_by(func.date(Bill.created_at)) \
            .all()

        labels = [str(r[0]) for r in revenue_by_day]
        values = [float(r[1]) for r in revenue_by_day]

        return render_template(
            "stats.html",
            total_revenue=total_revenue,
            total_bookings=total_bookings,
            labels=labels,
            values=values,
            category_stats=category_stats,
            cat_labels=cat_labels,
            cat_values=cat_values,
            this_month_rev=this_month_rev,
            last_month_rev=last_month_rev,
            growth_pct=growth_pct,
            start_date=start_date or "",
            end_date=end_date or "",
            today=today.strftime("%Y-%m-%d")
        )



    @app.route("/favorites")
    def favorites():
        return redirect(url_for("home", _anchor="favorites"))

    @app.route("/explore")
    def explore():
        return render_template("explore.html", username=session.get('username'))

    @app.route("/featured")
    def featured():
        featured_products = (Product.query.filter_by(active=True)
                             .order_by(Product.price.desc()).limit(6).all())
        return render_template("featured.html", products=featured_products, username=session.get('username'))


if __name__ == "__main__":
    register_routes(app=app)
    app.run(debug=True)