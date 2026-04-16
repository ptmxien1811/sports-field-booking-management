from flask import render_template, session, redirect, url_for, request, flash, jsonify
from bookingapp import app, db
from bookingapp.dao import (get_bookings_by_user, get_favorites_by_user,
                             get_slots_for_product_date, create_booking,
                             cancel_booking_by_id, toggle_favorite,
                             add_review, get_product_by_id)
from bookingapp.models import Product, User, Booking
from bookingapp import admin
from datetime import datetime, timedelta,date as date_type
import datetime as dt


# ===== HOME =====
@app.route("/")
def home():
    products = Product.query.filter_by(active=True).all()

    user_id = session.get("user_id")
    username = session.get("username")

    bookings = []
    favorites = []
    favorite_ids = []

    if user_id:
        bookings = get_bookings_by_user(user_id)
        favorites = get_favorites_by_user(user_id)

        favorite_ids = [f.product_id for f in favorites]

    return render_template("index.html",
                           products=products,
                           bookings=bookings,
                           favorites=favorites,
                           favorite_ids=favorite_ids,
                           username=username)

# ===== AUTH =====
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


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm  = request.form["confirm_password"]
        if password != confirm:
            return render_template("register.html", error="Mật khẩu không khớp")
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Tên đăng nhập đã tồn tại")
        user = User(username=username, password="")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


# ===== VENUE DETAIL =====
@app.route("/venue/<int:id>")
def venue_detail(id):
    product = get_product_by_id(id)
    return render_template("venue_detail.html", product=product,username=session.get("username"))


# ===== API: LẤY SLOTS THEO NGÀY =====
@app.route("/api/slots/<int:product_id>")
def api_slots(product_id):
    date_str = request.args.get("date", "")
    try:
        sel_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        sel_date = date_type.today()

    slots_data, available = get_slots_for_product_date(product_id, sel_date)
    return jsonify({"slots": slots_data, "available": available})


# ===== API: ĐẶT SÂN =====
@app.route("/api/book", methods=["POST"])
def api_book():
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

    # Kiểm tra đã đặt chưa
    exists = Booking.query.filter_by(
        product_id=product_id,
        slot_label=slot_label,
        date=datetime.combine(sel_date, datetime.min.time()),
    ).first()
    if exists:
        return jsonify({"ok": False, "msg": "Khung giờ này đã được đặt"}), 400

    b = create_booking(session["user_id"], product_id, slot_label, sel_date)
    return jsonify({
        "ok":         True,
        "booking_id": b.id,
        "msg":        f"Đặt sân thành công! Mã đặt: #{b.id}"
    })
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
    if not session.get("user_id"):
        return jsonify({"ok": False, "msg": "Vui lòng đăng nhập để đánh giá"}), 401

    data    = request.json
    rating  = int(data.get("rating", 5))
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"ok": False, "msg": "Vui lòng nhập nội dung đánh giá"}), 400

    r = add_review(session["user_id"], product_id, rating, content)
    return jsonify({
        "ok":       True,
        "author":   session["username"],
        "rating":   r.rating,
        "stars":    r.stars,
        "content":  r.content,
        "date_str": r.date_str,
    })


# ===== CANCEL BOOKING (form POST từ index.html) =====
@app.route("/api/cancel-booking/<int:id>", methods=["POST"])
def cancel_booking_final(id):
    booking = Booking.query.get(id)
    user_id = session.get("user_id")

    if not booking or booking.user_id != user_id:
        flash("Không tìm thấy hoặc bạn không có quyền!", "danger")
        return redirect(url_for("home", _anchor="booked"))

        # GIẢ LẬP GIỜ TEST: 7:30 sáng ngày 11/4
    now_time = datetime(2026, 3, 1, 8, 30)

    #đã qua giờ kết thúc
    if now_time > booking.end_time:
        flash("Đã sử dụng , không thể hủy!", "info")
        return redirect(url_for("home", _anchor="booked"))

    #đang trong giờ đá
    if booking.start_time <= now_time <= booking.end_time:
        flash("Đang trong giờ sử dụng, bạn không thể hủy lúc này!", "danger")
        return redirect(url_for("home", _anchor="booked"))

    #< 2 tiếng tới giờ đá
    if now_time < booking.start_time:
        if booking.start_time - now_time < timedelta(hours=2):
            flash("Sắp tới giờ sử dụng, không được hủy!", "warning")
            return redirect(url_for("home", _anchor="booked"))
    db.session.delete(booking)
    db.session.commit()

    flash("Hệ thống xác nhận: Đã hủy thành công!", "success")
    return redirect(url_for("home", _anchor="booked"))
@app.route("/favorites")
def favorites():
    return render_template("favorites.html",username=session.get('username'))

@app.route("/explore")
def explore():
    return render_template("explore.html",username=session.get('username'))

@app.route("/featured")
def featured():
    featured_products = (Product.query.filter_by(active=True)
                         .order_by(Product.price.desc()).limit(6).all())
    return render_template("featured.html", products=featured_products,username=session.get('username'))

@app.route("/account")
def account():
    return render_template("account.html")


if __name__ == "__main__":
    app.run(debug=True)