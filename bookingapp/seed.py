from bookingapp import db, app
from bookingapp.models import Category, Product, User, Booking, Favorite
from datetime import datetime, timedelta
import random

if __name__ == "__main__":
    with app.app_context():
        # Xóa dữ liệu cũ và tạo lại
        db.drop_all()
        db.create_all()

        # Thêm danh mục sân thể thao
        football_field = Category(name="Sân bóng đá", address="123 Nguyễn Văn Linh, Q7, TP.HCM", phone="0909123456")
        tennis_field = Category(name="Sân tennis", address="45 Lê Lợi, Q1, TP.HCM", phone="0909988776")
        swimming_pool = Category(name="Hồ bơi", address="88 Trần Hưng Đạo, Q5, TP.HCM", phone="0911222333")
        badminton_field = Category(name="Sân cầu lông", address="12 Lý Thường Kiệt, Q10, TP.HCM", phone="0909333444")
        basketball_field = Category(name="Sân bóng rổ", address="99 Nguyễn Huệ, Q1, TP.HCM", phone="0909555666")
        volleyball_field = Category(name="Sân bóng chuyền", address="22 Hai Bà Trưng, Q3, TP.HCM", phone="0909777888")
        tabletennis_field = Category(name="Sân bóng bàn", address="55 Nguyễn Trãi, Q5, TP.HCM", phone="0909666777")
        pickleball_field = Category(name="Sân pickleball", address="77 Lê Văn Sỹ, Q3, TP.HCM", phone="0909444555")

        db.session.add_all([
            football_field, tennis_field, swimming_pool,
            badminton_field, basketball_field, volleyball_field,
            tabletennis_field, pickleball_field
        ])
        db.session.commit()

        # Thêm sản phẩm
        products = [
            Product(name="Sân bóng đá mini 7 người", price=500000, image="football.jpg", category_id=football_field.id),
            Product(name="Sân tennis tiêu chuẩn", price=300000, image="tennis.jpg", category_id=tennis_field.id),
            Product(name="Hồ bơi 25m", price=200000, image="pool.jpg", category_id=swimming_pool.id),
            Product(name="Sân cầu lông tiêu chuẩn", price=150000, image="caulong.jpg", category_id=badminton_field.id),
            Product(name="Sân bóng rổ ngoài trời", price=250000, image="bongro.jpg", category_id=basketball_field.id),
            Product(name="Sân bóng chuyền", price=180000, image="bongchuyen.jpg", category_id=volleyball_field.id),
            Product(name="Sân bóng bàn", price=120000, image="bongban.jpg", category_id=tabletennis_field.id),
            Product(name="Sân pickleball hiện đại", price=200000, image="pickleball.jpg", category_id=pickleball_field.id)
        ]
        db.session.add_all(products)
        db.session.commit()

        # Thêm người dùng
        users = [
            User(username="admin", password="123456"),
            User(username="Phạm Thị Mỹ Xuyên", password="abc123"),
            User(username="Lý Đại Long", password="pass456"),
            User(username="Ngô Thị Thúy Quyên", password="pass789"),
        ]
        db.session.add_all(users)
        db.session.commit()

        # Thêm 50 booking
        for i in range(50):
            user_id = random.choice([u.id for u in users])
            product_id = random.choice([p.id for p in products])
            start_time = datetime(2026, 3, random.randint(25, 30), random.randint(6, 20), 0)
            end_time = start_time + timedelta(hours=2)
            status = random.choice(["confirmed", "cancelled", "pending"])
            booking = Booking(user_id=user_id, product_id=product_id,
                              start_time=start_time, end_time=end_time, status=status)
            db.session.add(booking)

        # Thêm 50 favorite
        for i in range(50):
            user_id = random.choice([u.id for u in users])
            product_id = random.choice([p.id for p in products])
            fav = Favorite(user_id=user_id, product_id=product_id)
            db.session.add(fav)

        db.session.commit()

        print("Dữ liệu mẫu đã được thêm thành công!")
