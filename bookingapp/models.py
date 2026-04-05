from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
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

    name = Column(String(50), nullable=False)
    products = relationship("Product", back_populates="category")

    def __str__(self):
        return self.name


# ================= USER =================
class User(BaseModel):
    __tablename__ = 'user'

    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    bookings = relationship("Booking", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# ================= PRODUCT =================
class Product(BaseModel):
    __tablename__ = 'products'

    name = Column(String(100), nullable=False, unique=True)
    price = Column(Float, default=0)
    image = Column(String(100))
    active = Column(Boolean, default=True)
    address = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)

    category = relationship("Category", back_populates="products")
    bookings = relationship("Booking", back_populates="product")
    favorites = relationship("Favorite", back_populates="product")

    def __str__(self):
        return self.name


# ================= BOOKING =================
class Booking(BaseModel):
    __tablename__ = 'booking'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="confirmed")

    user = relationship("User", back_populates="bookings")
    product = relationship("Product", back_populates="bookings")


# ================= FAVORITE =================
class Favorite(BaseModel):
    __tablename__ = 'favorite'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)

    user = relationship("User", back_populates="favorites")
    product = relationship("Product", back_populates="favorites")


# ================= MAIN =================
if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()