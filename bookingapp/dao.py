from bookingapp import db
from bookingapp.models import Booking, User, Product, Category, Favorite
from sqlalchemy.orm import joinedload

# ================= USER FILTER =================
def get_bookings_by_user(user_id):
    bookings = Booking.query.options(
        joinedload(Booking.product).joinedload(Product.category)
    ).filter(Booking.user_id == user_id).all()

    return bookings


def get_favorites_by_user(user_id):
    favorites = Favorite.query.options(
        joinedload(Favorite.product).joinedload(Product.category)
    ).filter(Favorite.user_id == user_id).all()

    return favorites
# ================= BOOKING =================
def get_all_bookings():
    bookings = Booking.query.options(
        joinedload(Booking.user),
        joinedload(Booking.product).joinedload(Product.category)
    ).all()

    result = []
    for b in bookings:
        result.append({
            "id": b.id,
            "username": b.user.username,
            "product_name": b.product.name,
            "category_name": b.product.category.name,
            "start_time": b.start_time,
            "end_time": b.end_time,
            "status": b.status
        })

    return result


# ================= FAVORITE =================
def get_all_favorites():
    favorites = Favorite.query.options(
        joinedload(Favorite.user),
        joinedload(Favorite.product).joinedload(Product.category)
    ).all()

    result = []
    for f in favorites:
        result.append({
            "id": f.id,
            "username": f.user.username,
            "product_name": f.product.name,
            "category_name": f.product.category.name
        })

    return result


# ================= CREATE BOOKING =================
def add_booking(user_id, product_id, start_time, end_time, status="confirmed"):
    booking = Booking(
        user_id=user_id,
        product_id=product_id,
        start_time=start_time,
        end_time=end_time,
        status=status
    )
    db.session.add(booking)
    db.session.commit()
    return booking


# ================= CREATE FAVORITE =================
def add_favorite(user_id, product_id):
    fav = Favorite(user_id=user_id, product_id=product_id)
    db.session.add(fav)
    db.session.commit()
    return fav


# ================= DELETE =================
def delete_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        db.session.delete(booking)
        db.session.commit()


def delete_favorite(fav_id):
    fav = Favorite.query.get(fav_id)
    if fav:
        db.session.delete(fav)
        db.session.commit()