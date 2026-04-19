from flask import render_template, session, redirect, url_for, request, flash, jsonify
from bookingapp import app, db
from bookingapp.dao import (get_bookings_by_user, get_favorites_by_user,
                             get_slots_for_product_date, create_booking,
                             cancel_booking_by_id, toggle_favorite,
                             add_review, get_product_by_id,
                             has_booked_product, has_reviewed_product)
from bookingapp.models import Product, User, Booking, Bill
from bookingapp import admin
from datetime import datetime, timedelta, date as date_type
import datetime as dt
import requests as http_requests
import os
from sqlalchemy import func

# ===== CẤU HÌNH GOOGLE OAUTH =====
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID",     "YOUR_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI",  "http://localhost:5000/auth/google/callback")

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"


# ===== HOME =====
@app.route("/")
def home():
    products     = Product.query.filter_by(active=True).all()
    user_id      = session.get("user_id")
    username     = session.get("username")
    bookings     = []
    favorites    = []
    favorite_ids = []
    if user_id:
        bookings     = get_bookings_by_user(user_id)
        favorites    = get_favorites_by_user(user_id)
        favorite_ids = [f.product_id for f in favorites]
    return render_template("index.html",
                           products=products,
                           bookings=bookings,
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
            session["user_id"]  = user.id
            session["username"] = user.username
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("home"))
        flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất!", "info")
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
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
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
        flash("Đăng nhập thành công!", "success")
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
        base = username
        i = 1
        while User.query.filter_by(username=username).first():
            username = f"{base}{i}"
            i += 1

        user = User(username=username, email=email, password="", auth_type='email')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("home"))
    return render_template("register.html")


# ===== AUTH: ĐĂNG NHẬP BẰNG SĐT =====
@app.route("/login/phone", methods=["GET", "POST"])
def login_phone():
    if request.method == "POST":
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        if not User.validate_phone(phone):
            return render_template("login.html", error="Số điện thoại không hợp lệ")
        user = User.query.filter_by(phone=phone).first()
        if not user or not user.check_password(password):
            return render_template("login.html", error="Số điện thoại hoặc mật khẩu không đúng")
        session["user_id"]  = user.id
        session["username"] = user.username
        flash("Đăng nhập thành công!", "success")
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
        base = username
        i = 1
        while User.query.filter_by(username=username).first():
            username = f"{base}{i}"
            i += 1

        user = User(username=username, phone=phone, password="", auth_type='phone')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
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
        flash("Đăng nhập Google thất bại!", "danger")
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
        flash("Không lấy được token từ Google!", "danger")
        return redirect(url_for("login"))

    user_res  = http_requests.get(GOOGLE_USER_URL,
                                   headers={"Authorization": f"Bearer {access_token}"})
    user_info = user_res.json()

    google_id    = user_info.get("sub")
    google_email = user_info.get("email")
    google_name  = user_info.get("name", "")

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=google_email).first()
        if user:
            user.google_id    = google_id
            user.google_email = google_email
            db.session.commit()
        else:
            username = google_name.replace(" ", "") or f"user_{google_id[:6]}"
            base = username
            i = 1
            while User.query.filter_by(username=username).first():
                username = f"{base}{i}"
                i += 1
            user = User(
                username=username, email=google_email,
                google_id=google_id, google_email=google_email,
                auth_type='google', password=""
            )
            db.session.add(user)
            db.session.commit()

    session["user_id"]  = user.id
    session["username"] = user.username
    flash(f"Chào mừng {user.username}! Đăng nhập Google thành công.", "success")
    return redirect(url_for("home"))


# ===== VENUE DETAIL =====
@app.route("/venue/<int:id>")
def venue_detail(id):
    product     = get_product_by_id(id)
    user_id     = session.get("user_id")
    can_review  = False
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

    # Trả về thêm thông tin về giới hạn đặt sân trong ngày của user
    user_id       = session.get("user_id")
    bookings_today = 0
    if user_id:
        day_start = datetime.combine(sel_date, datetime.min.time())
        day_end   = day_start + timedelta(days=1)
        bookings_today = Booking.query.filter(
            Booking.user_id == user_id,
            Booking.date    >= day_start,
            Booking.date    <  day_end,
            Booking.status  == "confirmed"
        ).count()

    slots_data, available = get_slots_for_product_date(product_id, sel_date)
    return jsonify({
        "slots":          slots_data,
        "available":      available,
        "bookings_today": bookings_today,   # số sân đã đặt hôm đó
        "max_per_day":    3,
    })


# ===== API: ĐẶT SÂN =====
@app.route("/api/book", methods=["POST"])
def api_book():
    # ── Ràng buộc 1: Phải đăng nhập ──────────────────────────────────────
    if not session.get("user_id"):
        return jsonify({"ok": False, "msg": "Vui lòng đăng nhập để đặt sân"}), 401

    data       = request.json
    product_id = data.get("product_id")
    slot_label = data.get("slot")
    date_str   = data.get("date")

    try:
        sel_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"ok": False, "msg": "Ngày không hợp lệ"}), 400

    b, err = create_booking(session["user_id"], product_id, slot_label, sel_date)
    if err:
        return jsonify({"ok": False, "msg": err}), 400

    return jsonify({"ok": True, "booking_id": b.id,
                    "msg": f"Đặt sân thành công! Mã đặt: #{b.id}"})


# ===== API: TOGGLE FAVORITE =====
@app.route("/api/favorite/<int:product_id>", methods=["POST"])
def api_favorite(product_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "msg": "Chưa đăng nhập"}), 401
    added = toggle_favorite(user_id, product_id)
    return jsonify({"ok": True, "added": added})


# ===== API: GỬI ĐÁNH GIÁ =====
@app.route("/api/review/<int:product_id>", methods=["POST"])
def api_review(product_id):
    # ── Phải đăng nhập ────────────────────────────────────────────────────
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
    booked      = has_booked_product(user_id, product_id)
    reviewed    = has_reviewed_product(user_id, product_id)
    return jsonify({
        "can_review":   booked and not reviewed,
        "has_reviewed": reviewed,
        "has_booked":   booked,
        "reason":       "ok" if (booked and not reviewed)
                        else ("already_reviewed" if reviewed else "not_booked")
    })


# ===== CANCEL BOOKING =====
@app.route("/api/cancel-booking/<int:id>", methods=["POST"])
def cancel_booking_final(id):
    booking  = Booking.query.get(id)
    user_id  = session.get("user_id")
    if not booking or booking.user_id != user_id:
        flash("Không tìm thấy hoặc bạn không có quyền!", "danger")
        return redirect(url_for("home", _anchor="booked"))
    now_time = datetime.now()
    if now_time > booking.end_time:
        flash("Đã sử dụng, không thể hủy!", "info")
        return redirect(url_for("home", _anchor="booked"))
    if booking.start_time <= now_time <= booking.end_time:
        flash("Đang trong giờ sử dụng, bạn không thể hủy lúc này!", "danger")
        return redirect(url_for("home", _anchor="booked"))
    if now_time < booking.start_time:
        if booking.start_time - now_time < timedelta(hours=2):
            flash("Sắp tới giờ sử dụng, không được hủy!", "warning")
            return redirect(url_for("home", _anchor="booked"))
    db.session.delete(booking)
    db.session.commit()
    flash("Hệ thống xác nhận: Đã hủy thành công!", "success")
    return redirect(url_for("home", _anchor="booked"))

@app.route("/stats")
def stats():
    start_date = request.args.get("start_date")
    end_date   = request.args.get("end_date")

    today = datetime.now().date()

    start = None
    end   = None

    # ===== XỬ LÝ START DATE =====
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()

        if start_dt > today:
            start_dt = today

        start = datetime.combine(start_dt, datetime.min.time())

    # ===== XỬ LÝ END DATE =====
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        if end_dt > today:
            end_dt = today

        end = datetime.combine(end_dt, datetime.min.time()) + timedelta(days=1)

    # ===== QUERY =====
    query = db.session.query(Bill)

    if start:
        query = query.filter(Bill.created_at >= start)

    if end:
        query = query.filter(Bill.created_at < end)

    bills = query.all()

    total_revenue = sum(b.amount for b in bills)
    total_bookings = len(bills)

    # ===== CHART =====
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
        .order_by(func.date(Bill.created_at).asc()) \
        .all()

    labels = [str(r[0]) for r in revenue_by_day]
    values = [float(r[1]) for r in revenue_by_day]

    return render_template(
        "stats.html",
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        labels=labels,
        values=values,
        start_date=start_date or "",
        end_date=end_date or "",
        today=today.strftime("%Y-%m-%d")
    )
@app.route("/favorites")
def favorites():
    return render_template("favorites.html", username=session.get('username'))

@app.route("/explore")
def explore():
    return render_template("explore.html", username=session.get('username'))

@app.route("/featured")
def featured():
    featured_products = (Product.query.filter_by(active=True)
                         .order_by(Product.price.desc()).limit(6).all())
    return render_template("featured.html", products=featured_products, username=session.get('username'))

@app.route("/account")
def account():
    return render_template("account.html")


if __name__ == "__main__":
    app.run(debug=True)