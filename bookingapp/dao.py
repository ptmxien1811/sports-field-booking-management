from bookingapp import db
from bookingapp.models import Booking, User, Product, Category, Favorite, Review, TimeSlot, Bill
from sqlalchemy.orm import joinedload
from datetime import datetime, date as date_type, timedelta
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
    """
    Tạo booking mới với đầy đủ ràng buộc:
    1. Người dùng phải đăng nhập (kiểm tra ở route)
    2. Không được đặt sân trong quá khứ
    3. Khung giờ đặt tối thiểu 1 giờ (TimeSlot luôn là 1h)
    4. Một người chỉ được đặt tối đa 3 sân/ngày
    5. Không được đặt nếu đã có người đặt cùng khung giờ

    Trả về (booking | None, error_message | None)
    """
    now = datetime.now()
    start_str, end_str = slot_label.split(" - ")
    start_time = datetime.combine(date_obj, datetime.strptime(start_str, "%H:%M").time())
    end_time   = datetime.combine(date_obj, datetime.strptime(end_str,   "%H:%M").time())

    # ── Ràng buộc 2: Không đặt trong quá khứ ──────────────────────────────
    if start_time <= now:
        return None, "Không thể đặt sân trong quá khứ hoặc khung giờ đã qua."

    # ── Ràng buộc 3: Khung giờ tối thiểu 1 giờ ────────────────────────────
    duration_hours = (end_time - start_time).seconds / 3600
    if duration_hours < 1:
        return None, "Khung giờ đặt phải tối thiểu 1 giờ."

    # ── Ràng buộc 4: Tối đa 3 sân/ngày ────────────────────────────────────
    day_start = datetime.combine(date_obj, datetime.min.time())
    day_end   = day_start + timedelta(days=1)
    bookings_today = Booking.query.filter(
        Booking.user_id    == user_id,
        Booking.date       >= day_start,
        Booking.date       <  day_end,
        Booking.status     == "confirmed"
    ).count()
    if bookings_today >= 3:
        return None, "Bạn đã đặt tối đa 3 sân trong ngày này."

    # ── Ràng buộc 5: Trùng khung giờ (cùng sân) ───────────────────────────
    conflict = Booking.query.filter(
        Booking.product_id == product_id,
        Booking.slot_label == slot_label,
        Booking.date       == day_start,
        Booking.status     == "confirmed"
    ).first()
    if conflict:
        return None, "Khung giờ này đã được đặt bởi người khác."

    b = Booking(
        user_id    = user_id,
        product_id = product_id,
        slot_label = slot_label,
        date       = day_start,
        start_time = start_time,
        end_time   = end_time,
        status     = "confirmed"
    )
    db.session.add(b)
    db.session.commit()
    return b, None


def cancel_booking_by_id(booking_id, user_id):
    booking = Booking.query.get(booking_id)

    if not booking or booking.user_id != user_id:
        return False

    if booking.status == "cancelled":
        return False

    now_time = datetime.now()

    if now_time > booking.end_time:
        return False

    if booking.start_time <= now_time <= booking.end_time:
        return False

    if now_time < booking.start_time:
        if booking.start_time - now_time < timedelta(hours=2):
            return False

    slot = TimeSlot.query.filter_by(
        product_id=booking.product_id,
        label=booking.slot_label
    ).first()

    if slot:
        slot.active = True

    existing_bill = Bill.query.filter_by(booking_id=booking_id).first()
    if existing_bill:
        db.session.delete(existing_bill)
    # qua hết các chốt chặn trên thì mới hủy
    booking.status = "cancelled"
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

    total_slots  = len(slots)
    booked_count = len(booked_labels)
    available    = total_slots - booked_count

    return result, available


# ===== FAVORITES =====
def get_favorites_by_user(user_id):
    return (Favorite.query
            .options(joinedload(Favorite.product).joinedload(Product.category))
            .filter(Favorite.user_id == user_id)
            .all())


def toggle_favorite(user_id, product_id):
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


def has_booked_product(user_id, product_id):
    """Kiểm tra user đã từng đặt sân này chưa (kể cả cancelled)"""
    return Booking.query.filter(
        Booking.user_id    == user_id,
        Booking.product_id == product_id
    ).first() is not None


def has_reviewed_product(user_id, product_id):
    """Kiểm tra user đã review sân này chưa"""
    return Review.query.filter_by(
        user_id    = user_id,
        product_id = product_id
    ).first() is not None


def add_review(user_id, product_id, rating, content):
    """
    Ràng buộc đánh giá:
    - Phải đã đặt sân này ít nhất 1 lần
    - Chưa từng review sân này
    - Rating từ 1-5
    Trả về (review | None, error_msg | None)
    """
    if not has_booked_product(user_id, product_id):
        return None, "Chỉ những người đã đặt sân này mới được đánh giá."

    if has_reviewed_product(user_id, product_id):
        return None, "Bạn đã đánh giá sân này rồi."

    rating = max(1, min(5, int(rating)))

    r = Review(user_id=user_id, product_id=product_id,
               rating=rating, content=content)
    db.session.add(r)
    db.session.commit()
    return r, None


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