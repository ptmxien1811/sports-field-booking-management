from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from bookingapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class BaseModel(db.Model):
    __abstract__ = True
    id = Column(db.Integer, primary_key=True, autoincrement=True)

class Category(BaseModel):
    __tablename__ = 'category'
    name = Column(db.String(50), nullable=False)
    address = Column(db.String(50), nullable=False)
    phone = Column(db.String(50), nullable=False)
    product = relationship("Product", backref="category", lazy=True)

    def __str__(self):
        return self.name

class User(BaseModel):
    __tablename__ = 'user'
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(80), nullable=False)

    bookings = relationship("Booking", backref="user", lazy=True)
    favorites = relationship("Favorite", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(BaseModel):
    __tablename__ = 'products'
    name = Column(String(100), nullable=False)
    price = Column(Float, default=0)
    image = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now())
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)

    bookings = relationship("Booking", backref="product", lazy=True)
    favorites = relationship("Favorite", backref="product", lazy=True)

    def __str__(self):
        return self.name

# Bảng Sân đã đặt
class Booking(BaseModel):
    __tablename__ = 'booking'
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="confirmed")  # confirmed, cancelled, pending

# Bảng Sân yêu thích
class Favorite(BaseModel):
    __tablename__ = 'favorite'
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
