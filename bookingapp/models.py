from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from bookingapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


# ================= CATEGORY =================
class Category(BaseModel):
    __tablename__ = 'category'
    name    = Column(String(100), nullable=False)
    address = Column(String(200), nullable=True)
    phone   = Column(String(50),  nullable=True)
    products = relationship("Product", back_populates="category")

    def __str__(self):
        return self.name


# ================= USER =================
class User(BaseModel):
    __tablename__ = 'user'

    username     = Column(String(80),  unique=True, nullable=False)
    password     = Column(String(255), nullable=True)          # nullable vì Google login không có password
    email        = Column(String(120), unique=True, nullable=True)
    phone        = Column(String(20),  unique=True, nullable=True)
    avatar       = Column(String(200), default="default_avatar.png")

    # Google OAuth
    google_id    = Column(String(100), unique=True, nullable=True)
    google_email = Column(String(120), nullable=True)

    # Loại tài khoản: 'local' | 'google' | 'email' | 'phone'
    auth_type    = Column(String(20),  default='local')

    created_at   = Column(DateTime, default=datetime.now)

    bookings  = relationship("Booking",  back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    reviews   = relationship("Review",   back_populates="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if not self.password:
            return False
        return check_password_hash(self.password, password)

    @staticmethod
    def validate_password(password):
        """
        Ràng buộc mật khẩu:
        - Ít nhất 8 ký tự
        - Có chữ hoa
        - Có chữ thường
        - Có số
        - Có ký tự đặc biệt
        Trả về (ok: bool, message: str)
        """
        errors = []
        if len(password) < 8:
            errors.append("ít nhất 8 ký tự")
        if not re.search(r'[A-Z]', password):
            errors.append("ít nhất 1 chữ HOA")
        if not re.search(r'[a-z]', password):
            errors.append("ít nhất 1 chữ thường")
        if not re.search(r'\d', password):
            errors.append("ít nhất 1 chữ số")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
            errors.append("ít nhất 1 ký tự đặc biệt (!@#$%...)")
        if errors:
            return False, "Mật khẩu cần có: " + ", ".join(errors)
        return True, "OK"

    @staticmethod
    def validate_email(email):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_phone(phone):
        # Số điện thoại VN: 10 số, bắt đầu bằng 0
        pattern = r'^(0[3-9][0-9]{8})$'
        return bool(re.match(pattern, phone))


# ================= AMENITY / TIMESLOT / PRODUCT =================
class Amenity(BaseModel):
    __tablename__ = 'amenity'
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    icon       = Column(String(10))
    label      = Column(String(100))
    product    = relationship("Product", back_populates="amenities")


class TimeSlot(BaseModel):
    __tablename__ = 'time_slot'
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    period     = Column(String(20))
    label      = Column(String(20))
    product    = relationship("Product", back_populates="time_slots")

    def __str__(self):
        return self.label


class Product(BaseModel):
    __tablename__ = 'products'
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")
    price       = Column(Float, default=0)
    image       = Column(String(100))
    active      = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.now)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    address = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)

    category   = relationship("Category",  back_populates="products")
    bookings   = relationship("Booking",   back_populates="product", cascade="all, delete-orphan")
    favorites  = relationship("Favorite",  back_populates="product", cascade="all, delete-orphan")
    amenities  = relationship("Amenity",   back_populates="product", cascade="all, delete-orphan")
    time_slots = relationship("TimeSlot",  back_populates="product", cascade="all, delete-orphan")
    reviews    = relationship("Review",    back_populates="product", cascade="all, delete-orphan")

    @property
    def avg_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    def __str__(self):
        return self.name


# ================= BOOKING =================
class Booking(BaseModel):
    __tablename__ = 'booking'
    user_id    = Column(Integer, ForeignKey('user.id'),     nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    slot_label = Column(String(20))
    date       = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time   = Column(DateTime, nullable=False)
    status     = Column(String(20), default="confirmed")

    user    = relationship("User",    back_populates="bookings")
    product = relationship("Product", back_populates="bookings")


# ================= FAVORITE =================
class Favorite(BaseModel):
    __tablename__ = 'favorite'
    user_id    = Column(Integer, ForeignKey('user.id'),     nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    user    = relationship("User",    back_populates="favorites")
    product = relationship("Product", back_populates="favorites")


# ================= REVIEW =================
class Review(BaseModel):
    __tablename__ = 'review'
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id    = Column(Integer, ForeignKey('user.id'),     nullable=False)
    rating     = Column(Integer, default=5)
    content    = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    product = relationship("Product", back_populates="reviews")
    user    = relationship("User",    back_populates="reviews")

    @property
    def date_str(self):
        delta = datetime.now() - self.created_at
        if delta.days == 0:  return "Hôm nay"
        if delta.days == 1:  return "1 ngày trước"
        if delta.days < 7:   return f"{delta.days} ngày trước"
        if delta.days < 30:  return f"{delta.days // 7} tuần trước"
        return f"{delta.days // 30} tháng trước"

    @property
    def stars(self):
        return "★" * self.rating + "☆" * (5 - self.rating)

# ===== BILL =====
class Bill(BaseModel):
    __tablename__ = 'bill'

    user_id    = Column(Integer, ForeignKey('user.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    amount     = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user    = relationship("User")
    product = relationship("Product")

    def __str__(self):
        return f"Bill #{self.id} - {self.amount}"


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()