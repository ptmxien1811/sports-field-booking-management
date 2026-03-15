from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from bookingapp import db, app
from sqlalchemy.orm import relationship
from datetime import datetime

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
    username = Column( String(80), unique=True, nullable=False)
    password = Column( String(80), nullable=False)

class Product(BaseModel):
    __tablename__ = 'products'
    name = Column( String(100), nullable=False)
    price = Column( Float, default=0)
    image = Column( String(100))
    active = Column( Boolean, default=True)
    created_at = Column( DateTime, default=datetime.now())
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)

    def __str__(self):
        return self.name

if __name__ == "__main__":
    with app.app_context():
        db.create_all()




