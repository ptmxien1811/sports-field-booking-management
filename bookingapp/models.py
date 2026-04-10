from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text
from bookingapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


# ================= CATEGORY =================
class Category(BaseModel):
    __tablename__ = 'category'
    name    = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    phone   = Column(String(50),  nullable=False)
    products = relationship("Product", back_populates="category")

    def __str__(self):
        return self.name


# ================= USER =================
class User(BaseModel):
    __tablename__ = 'user'

    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    avatar   = Column(String(200), default="default_avatar.png")

    bookings  = relationship("Booking",  back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    reviews   = relationship("Review",   back_populates="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Amenity(BaseModel):
    __tablename__ = 'amenity'
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    icon       = Column(String(10))
    label      = Column(String(100))
    product    = relationship("Product", back_populates="amenities")


class TimeSlot(BaseModel):
    __tablename__ = 'time_slot'
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    period     = Column(String(20))   # morning / afternoon / evening
    label      = Column(String(20))   # "08:00 - 09:00"
    product    = relationship("Product", back_populates="time_slots")


class Product(BaseModel):
    __tablename__ = 'products'
    name        = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")
    price       = Column(Float, default=0)
    image       = Column(String(100))
    active      = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.now)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)

    category   = relationship("Category",  back_populates="products")
    bookings   = relationship("Booking",   back_populates="product")
    favorites  = relationship("Favorite",  back_populates="product")
    amenities  = relationship("Amenity",   back_populates="product")
    time_slots = relationship("TimeSlot",  back_populates="product")
    reviews    = relationship("Review",    back_populates="product")

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
    slot_label = Column(String(20))          # "08:00 - 09:00"
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


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()