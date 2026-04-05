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
        football_field = Category(name="Sân bóng đá")
        tennis_field = Category(name="Sân tennis")
        swimming_pool = Category(name="Hồ bơi")
        badminton_field = Category(name="Sân cầu lông")
        basketball_field = Category(name="Sân bóng rổ")
        volleyball_field = Category(name="Sân bóng chuyền")
        tabletennis_field = Category(name="Sân bóng bàn")
        pickleball_field = Category(name="Sân pickleball")

        db.session.add_all([
            football_field, tennis_field, swimming_pool,
            badminton_field, basketball_field, volleyball_field,
            tabletennis_field, pickleball_field
        ])
        db.session.commit()

        # Thêm sản phẩm
        products = [
            Product(name="Sân bóng đá mini 7 người", price=500000, image="football.jpg",
                    address="123 Nguyễn Văn Linh, Q7, TP.HCM", phone="0909123456", category_id=football_field.id),

            Product(name="Sân tennis tiêu chuẩn màu xanh", price=300000, image="tennis.jpg",
                    address="45 Lê Lợi, Q1, TP.HCM", phone="0909988776", category_id=tennis_field.id),

            Product(name="Hồ bơi 125m", price=200000, image="pool.jpg",
                    address="88 Trần Hưng Đạo, Q5, TP.HCM", phone="0911222333", category_id=swimming_pool.id),

            Product(name="Sân cầu lông tiêu chuẩn 5 sao", price=150000, image="caulong.jpg",
                    address="12 Lý Thường Kiệt, Q10, TP.HCM", phone="0909333444", category_id=badminton_field.id),

            Product(name="Sân bóng rổ ngoài trời A", price=250000, image="bongro.jpg",
                    address="99 Nguyễn Huệ, Q1, TP.HCM", phone="0909555666", category_id=basketball_field.id),

            Product(name="Sân bóng chuyền siêu rộng", price=180000, image="bongchuyen.jpg",
                    address="22 Hai Bà Trưng, Q3, TP.HCM", phone="0909777888", category_id=volleyball_field.id),

            Product(name="Sân bóng bàn 2 bàn", price=120000, image="bongban.jpg",
                    address="55 Nguyễn Trãi, Q5, TP.HCM", phone="0909666777", category_id=tabletennis_field.id),

            Product(name="Sân pickleball hiện đại", price=200000, image="pickleball.jpg",
                    address="77 Lê Văn Sỹ, Q3, TP.HCM", phone="0909444555", category_id=pickleball_field.id),

            Product(name="Sân bóng đá 11 người", price=800000, image="football.jpg",
                    address="200 Phạm Văn Đồng, TP.Thủ Đức, TP.HCM", phone="0911000111", category_id=football_field.id),

            Product(name="Sân tennis tiêu chuẩn màu vàng", price=300000, image="tennis.jpg",
                    address="15 Điện Biên Phủ, Bình Thạnh, TP.HCM", phone="0911222444", category_id=tennis_field.id),

            Product(name="Sân tennis cao cấp", price=500000, image="tennis.jpg",
                    address="300 Võ Văn Tần, Q3, TP.HCM", phone="0911333555", category_id=tennis_field.id),

            Product(name="Hồ bơi 25m", price=200000, image="pool.jpg",
                    address="50 Nguyễn Đình Chiểu, Q1, TP.HCM", phone="0911444666", category_id=swimming_pool.id),

            Product(name="Hồ bơi Olympic 50m", price=600000, image="pool.jpg",
                    address="10 Trường Chinh, Tân Bình, TP.HCM", phone="0911555777", category_id=swimming_pool.id),

            Product(name="Sân cầu lông tiêu chuẩn hạng A", price=150000, image="caulong.jpg",
                    address="88 Cộng Hòa, Tân Bình, TP.HCM", phone="0911666888", category_id=badminton_field.id),

            Product(name="Sân cầu lông đôi", price=200000, image="caulong.jpg",
                    address="66 Hoàng Văn Thụ, Phú Nhuận, TP.HCM", phone="0911777999", category_id=badminton_field.id),

            Product(name="Sân bóng rổ ngoài trời B", price=250000, image="bongro.jpg",
                    address="25 Nguyễn Thị Minh Khai, Q1, TP.HCM", phone="0911888000", category_id=basketball_field.id),

            Product(name="Sân bóng rổ trong nhà", price=400000, image="bongro.jpg",
                    address="120 Lê Văn Việt, TP.Thủ Đức, TP.HCM", phone="0911999111", category_id=basketball_field.id),

            Product(name="Sân bóng chuyền", price=180000, image="bongchuyen.jpg",
                    address="33 Phan Xích Long, Phú Nhuận, TP.HCM", phone="0922000222",
                    category_id=volleyball_field.id),

            Product(name="Sân bóng chuyền bãi biển", price=300000, image="bongchuyen.jpg",
                    address="1 Nguyễn Tất Thành, Q4, TP.HCM", phone="0922111333", category_id=volleyball_field.id),

            Product(name="Sân bóng bàn 4 bàn", price=120000, image="bongban.jpg",
                    address="78 Lý Tự Trọng, Q1, TP.HCM", phone="0922222444", category_id=tabletennis_field.id),

            Product(name="Sân bóng bàn đôi", price=180000, image="bongban.jpg",
                    address="90 Pasteur, Q1, TP.HCM", phone="0922333555", category_id=tabletennis_field.id),

            Product(name="Sân pickleball hiện đại mới nhất", price=200000, image="pickleball.jpg",
                    address="12 Nguyễn Oanh, Gò Vấp, TP.HCM", phone="0922444666", category_id=pickleball_field.id),

            Product(name="Sân pickleball tiêu chuẩn", price=250000, image="pickleball.jpg",
                    address="45 Quang Trung, Gò Vấp, TP.HCM", phone="0922555777", category_id=pickleball_field.id)
        ]
        db.session.add_all(products)
        db.session.commit()

        # Thêm người dùng
        users = [
            User(username="admin"),
            User(username="Phạm Thị Mỹ Xuyên"),
            User(username="Lý Đại Long"),
            User(username="Ngô Thị Thúy Quyên"),
            User(username="Nguyễn Văn Kiên"),
            User(username="Trần Thị Tú"),
            User(username="Lê Văn Kha"),
            User(username="Hoàng Thị Diệu"),
            User(username="Phạm Văn Anh"),
            User(username="Đỗ Thị Hòa")
        ]

        # Thiết lập mật khẩu cho từng user
        users[0].set_password("123456")
        users[1].set_password("abc123")
        users[2].set_password("pass456")
        users[3].set_password("pass789")
        users[4].set_password("user123")
        users[5].set_password("user456")
        users[6].set_password("user789")
        users[7].set_password("userabc")
        users[8].set_password("userefg")
        users[9].set_password("userxyz")

        # Lưu vào database
        db.session.add_all(users)
        db.session.commit()

        # Thêm 50 booking với dữ liệu khác nhau
        for i in range(50):
            user = random.choice(users)
            product = random.choice(products)
            start_day = random.randint(1, 28)
            start_hour = random.randint(6, 20)
            start_time = datetime(2026, 4                              , start_day, start_hour, 0)
            end_time = start_time + timedelta(hours=random.choice([1, 2, 3]))
            status = random.choice(["confirmed", "cancelled", "pending"])

            booking = Booking(
                user_id=user.id,
                product_id=product.id,
                start_time=start_time,
                end_time=end_time,
                status=status
            )
            db.session.add(booking)

        # Thêm 50 favorite
        for i in range(50):
            user = random.choice(users)
            product = random.choice(products)
            fav = Favorite(user_id=user.id, product_id=product.id)
            db.session.add(fav)

        db.session.commit()

        print("Dữ liệu mẫu đã được thêm thành công!")
