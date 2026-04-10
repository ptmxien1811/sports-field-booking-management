from bookingapp import db
from bookingapp.models import Booking, User, Product, Category, Favorite, Review, TimeSlot
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import func


# ===== USER =====
def get_user_by_id(user_id):
    return db.session.get(User, user_id)


# ===== BOOKINGS =====
def get_bookings_by_user(user_id):
    return (Booking.query
            .options(joinedload(Booking.product).joinedload(Product.category))
            .filter(Booking.user_id == user_id)
            .order_by(Booking.date.desc())
            .all())


def get_all_bookings():
    bookings = (Booking.query
                .options(joinedload(Booking.user),
                         joinedload(Booking.product).joinedload(Product.category))
                .all())
    return [{
        "id":            b.id,
        "username":      b.user.username,
        "product_name":  b.product.name,
        "category_name": b.product.category.name,
        "slot_label":    b.slot_label,
        "date":          b.date,
        "status":        b.status,
    } for b in bookings]


def create_booking(user_id, product_id, slot_label, date_obj):
    """Tạo booking mới. date_obj là datetime.date"""
    start_str, end_str = slot_label.split(" - ")
    start_time = datetime.combine(date_obj, datetime.strptime(start_str, "%H:%M").time())
    end_time   = datetime.combine(date_obj, datetime.strptime(end_str,   "%H:%M").time())

    b = Booking(
        user_id=user_id,
        product_id=product_id,
        slot_label=slot_label,
        date=datetime.combine(date_obj, datetime.min.time()),
        start_time=start_time,
        end_time=end_time,
        status="confirmed"
    )
    db.session.add(b)
    db.session.commit()
    return b


def cancel_booking_by_id(booking_id, user_id):
    b = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
    if not b:
        return False
    b.status = "cancelled"
    db.session.commit()
    return True


# ===== SLOTS =====
def get_slots_for_product_date(product_id, date_obj):
    """Trả về dict: {period: [{label, booked}]} và số slot trống"""
    slots = TimeSlot.query.filter_by(product_id=product_id).all()

    booked_labels = {
        b.slot_label for b in Booking.query.filter(
            Booking.product_id == product_id,
            Booking.date == datetime.combine(date_obj, datetime.min.time()),
            Booking.status == "confirmed"
        ).all()
    }

    result = {}
    for s in slots:
        result.setdefault(s.period, []).append({
            "label":  s.label,
            "booked": s.label in booked_labels
        })

    total_slots   = len(slots)
    booked_count  = len(booked_labels)
    available     = total_slots - booked_count

    return result, available


# ===== FAVORITES =====
def get_favorites_by_user(user_id):
    return (Favorite.query
            .options(joinedload(Favorite.product).joinedload(Product.category))
            .filter(Favorite.user_id == user_id)
            .all())


def toggle_favorite(user_id, product_id):
    """Thêm nếu chưa có, xóa nếu đã có. Trả về True=đã thêm, False=đã xóa"""
    fav = Favorite.query.filter_by(user_id=user_id, product_id=product_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        return False
    db.session.add(Favorite(user_id=user_id, product_id=product_id))
    db.session.commit()
    return True


def get_all_favorites():
    favs = (Favorite.query
            .options(joinedload(Favorite.user),
                     joinedload(Favorite.product).joinedload(Product.category))
            .all())
    return [{"id": f.id, "username": f.user.username,
             "product_name": f.product.name,
             "category_name": f.product.category.name} for f in favs]


# ===== REVIEWS =====
def get_reviews_by_product(product_id):
    return (Review.query
            .options(joinedload(Review.user))
            .filter_by(product_id=product_id)
            .order_by(Review.created_at.desc())
            .all())


def add_review(user_id, product_id, rating, content):
    r = Review(user_id=user_id, product_id=product_id,
               rating=rating, content=content)
    db.session.add(r)
    db.session.commit()
    return r


# ===== PRODUCTS =====
def get_product_by_id(product_id):
    return (Product.query
            .options(
                joinedload(Product.category),
                joinedload(Product.amenities),
                joinedload(Product.time_slots),
                joinedload(Product.reviews).joinedload(Review.user),
            )
            .filter_by(id=product_id)
            .first_or_404())