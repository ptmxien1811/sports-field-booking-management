from flask import render_template, session, redirect, url_for, request, flash
from bookingapp import app, db
import datetime

from bookingapp.dao import get_bookings_by_user, get_favorites_by_user
from bookingapp.models import Product, User, Booking
from bookingapp import admin

@app.route("/")
def home():
    now = datetime.datetime.now().strftime("Tuesday, %d/%m/%Y %H:%M")
    products = Product.query.all()
    username = session.get("username")
    user_id = session.get("user_id")
    bookings = []
    favorites = []
    if user_id:
        bookings = get_bookings_by_user(user_id)
        favorites = get_favorites_by_user(user_id)

    return render_template("index.html",
                           current_time=now,
                           products=products,
                           bookings=bookings,
                           favorites=favorites,
                           username=username)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("home"))
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")
            return redirect(url_for("login"))

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
        confirm = request.form["confirm_password"]

        if password != confirm:
            return render_template("register.html", error="Mật khẩu không khớp")
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="Tên đăng nhập đã tồn tại")

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Các trang khác

@app.route("/booked")
def booked():
    return render_template("booked.html")
@app.route("/cancel-booking/<int:id>", methods=["POST"])
def cancel_booking(id):
    booking = Booking.query.get(id)
    if booking:
        db.session.delete(booking)
        db.session.commit()
    return redirect(url_for("home"))

@app.route("/favorites")
def favorites():
    return render_template("favorites.html")

@app.route("/explore")
def explore():
    return render_template("explore.html")

@app.route("/featured")
def featured():
    # chọn 3 sân có giá cao nhất hoặc mới nhất làm nổi bật
    featured_products = Product.query.filter_by(active=True).order_by(Product.price.desc()).limit(6).all()
    return render_template("featured.html",
                           products=featured_products)



@app.route("/account")
def account():
    return render_template("account.html")

if __name__ == "__main__":
    app.run(debug=True)
