from bookingapp import db, app
from bookingapp.models import (Category, Product, User, Booking,
                                Favorite, Amenity, TimeSlot, Review, Bill)
from datetime import datetime, timedelta
import random

MORNING   = ["06:00 - 07:00","07:00 - 08:00","08:00 - 09:00",
             "09:00 - 10:00","10:00 - 11:00","11:00 - 12:00"]
AFTERNOON = ["13:00 - 14:00","14:00 - 15:00","15:00 - 16:00",
             "16:00 - 17:00","17:00 - 18:00","18:00 - 19:00"]
EVENING   = ["19:00 - 20:00","20:00 - 21:00","21:00 - 22:00"]


def add_slots(product, morning=True, afternoon=True, evening=True):
    if morning:
        for s in MORNING:
            db.session.add(TimeSlot(product_id=product.id, period='morning',   label=s))
    if afternoon:
        for s in AFTERNOON:
            db.session.add(TimeSlot(product_id=product.id, period='afternoon', label=s))
    if evening:
        for s in EVENING:
            db.session.add(TimeSlot(product_id=product.id, period='evening',   label=s))


def add_amenities(product, items):
    for icon, label in items:
        db.session.add(Amenity(product_id=product.id, icon=icon, label=label))


if __name__ == "__main__":
    with app.app_context():
        # Xóa dữ liệu cũ và tạo lại
        db.drop_all()
        db.create_all()

        # ===== CATEGORIES =====
        cat_football   = Category(id=1, name="Sân bóng đá")
        cat_tennis     = Category(id=2, name="Sân tennis")
        cat_badminton  = Category(id=3, name="Sân cầu lông")

        db.session.add_all([cat_football, cat_tennis, cat_badminton])
        db.session.commit()

        # ===== PRODUCTS =====
        # --- Bóng đá ---
        p1 = Product(name="Sân bóng đá mini 7 người", price=500000, image="football.jpg",
                     category_id=cat_football.id,
                     description="Sân cỏ nhân tạo thế hệ mới FIFA Quality Pro, đèn LED 1000W, hệ thống tưới tự động. Phù hợp cho các trận đấu phong trào và giải đấu nhỏ.")
        p2 = Product(name="Sân bóng đá 11 người", price=800000, image="football.jpg",
                     category_id=cat_football.id,
                     description="Sân cỏ tự nhiên chuẩn FIFA, kích thước 100x68m, hệ thống thoát nước tốt, khán đài 500 chỗ ngồi. Lý tưởng cho các giải đấu chính thức.")
        # --- Tennis ---
        p3 = Product(name="Sân tennis tiêu chuẩn màu xanh", price=300000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     description="Mặt sân Plexicushion xanh chuẩn ATP, hệ thống chiếu sáng 800 lux, phù hợp thi đấu ban đêm. Bao gồm ghế trọng tài và bảng tính điểm điện tử.")
        p4 = Product(name="Sân tennis tiêu chuẩn màu vàng", price=300000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     description="Mặt sân Plexicushion vàng chống trượt, hệ thống lưới căng tự động, phù hợp cho tập luyện và thi đấu phong trào hàng ngày.")
        p5 = Product(name="Sân tennis cao cấp", price=500000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     description="Sân tennis VIP mặt sân đất nện (clay) nhập khẩu từ Châu Âu, phòng thay đồ riêng, huấn luyện viên hỗ trợ theo yêu cầu.")

        # --- Cầu lông ---
        p6 = Product(name="Sân cầu lông tiêu chuẩn 5 sao", price=150000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     description="Sân cầu lông sàn gỗ PVC chuyên dụng, đèn LED 1200 lux không chói mắt, điều hòa 2 chiều mát lạnh. Đạt chuẩn BWF cho thi đấu quốc tế.")
        p7 = Product(name="Sân cầu lông tiêu chuẩn hạng A", price=150000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     description="Sàn vinyl cao su chuyên dụng, hệ thống lưới căng chuẩn, điều hòa inverter tiết kiệm điện. Phù hợp luyện tập hàng ngày cho mọi trình độ.")
        p8 = Product(name="Sân cầu lông đôi", price=200000, image="caulong.jpg",
                      category_id=cat_badminton.id,
                      description="Khu sân cầu lông đôi ghép 2 sân, lý tưởng cho câu lạc bộ và nhóm bạn. Có phòng thay đồ riêng biệt cho nam và nữ.")

        all_products = [p1,p2,p3,p4,p5,p6,p7,p8]
        db.session.add_all(all_products)
        db.session.commit()

        # ===== AMENITIES =====
        amenities_map = {
            p1.id:  [("⚽","Cỏ nhân tạo FIFA"),("💡","Đèn LED 1000W"),("🚗","Gửi xe miễn phí"),("🚿","Phòng tắm nóng lạnh"),("☕","Căng tin & Cà phê")],
            p2.id:  [("⚽","Cỏ tự nhiên chuẩn FIFA"),("🏟","Khán đài 500 chỗ"),("🚗","Bãi đậu xe rộng"),("🚿","Phòng thay đồ VIP"),("🎙","Hệ thống loa"),("☕","Căng tin")],
            p3.id:  [("🎾","Mặt sân Plexicushion"),("💡","Chiếu sáng 800 lux"),("🚗","Gửi xe miễn phí"),("🚿","Phòng tắm"),("📶","Wifi tốc độ cao")],
            p4.id:  [("🎾","Mặt sân chống trượt"),("💡","Đèn ban đêm"),("🚗","Gửi xe miễn phí"),("🥤","Nước miễn phí"),("📶","Wifi")],
            p5.id:  [("🎾","Sân clay nhập khẩu"),("👨‍🏫","HLV hỗ trợ"),("🚗","Gửi xe VIP"),("🚿","Phòng thay đồ riêng"),("☕","Cafe miễn phí"),("📶","Wifi")],
            p6.id:  [("🏸","Sàn PVC chuẩn BWF"),("❄️","Điều hòa 2 chiều"),("💡","Đèn 1200 lux"),("🚗","Gửi xe miễn phí"),("🏸","Cho thuê vợt")],
            p7.id:  [("🏸","Sàn vinyl cao su"),("❄️","Điều hòa inverter"),("🚗","Gửi xe"),("🏸","Cho thuê vợt & cầu"),("📶","Wifi")],
            p8.id: [("🏸","Khu sân đôi"),("🚿","Phòng thay đồ riêng"),("❄️","Điều hòa"),("🚗","Gửi xe"),("☕","Căng tin")],
            }
        for product_id, items in amenities_map.items():
            add_amenities(db.session.get(Product, product_id), items)

        # ===== TIME SLOTS =====
        for p in [p1, p2]:
            add_slots(p, morning=True, afternoon=True, evening=True)
        for p in [p3, p4, p5]:
            add_slots(p, morning=True, afternoon=True, evening=False)
            add_slots(p, morning=True, afternoon=True, evening=False)
        for p in [p6, p7, p8]:
            add_slots(p, morning=True, afternoon=True, evening=True)

        db.session.commit()

        # ===== USERS =====
        users_data = [
            ("admin",              "123456"),
            ("Phạm Thị Mỹ Xuyên", "abc123"),
            ("Lý Đại Long",        "pass456"),
            ("Ngô Thị Thúy Quyên","pass789"),
            ("Nguyễn Văn Kiên",    "user123"),
            ("Trần Thị Tú",        "user456"),
            ("Lê Văn Kha",         "user789"),
            ("Hoàng Thị Diệu",     "userabc"),
            ("Phạm Văn Anh",       "userefg"),
            ("Đỗ Thị Hòa",         "userxyz"),
        ]
        users = []
        for uname, pwd in users_data:
            u = User(username=uname, password="")
            u.set_password(pwd)
            db.session.add(u)
            users.append(u)
        db.session.commit()

        # ===== REVIEWS =====
        reviews_data = [
            # (product, user_index, rating, content, days_ago)
            (p1,  1, 5, "Sân cỏ rất đẹp, mịn mượt, đèn sáng rõ. Nhân viên thân thiện. Sẽ quay lại!", 2),
            (p1,  2, 4, "Giá hợp lý, bãi xe rộng. Cỏ hơi cứng một chút nhưng chơi được.", 5),
            (p1,  3, 5, "Tuyệt vời! Nhóm mình đặt mỗi tuần, chưa bao giờ thất vọng.", 10),
            (p2,  4, 5, "Sân 11 người chuẩn quá, cỏ tự nhiên xanh mướt, rất chuyên nghiệp.", 1),
            (p2,  5, 4, "Sân lớn, thoáng. Chỉ hơi xa trung tâm một chút.", 7),
            (p3,  1, 5, "Mặt sân Plexicushion cực kỳ tốt, không trượt, bóng nảy đều.", 3),
            (p3,  6, 4, "Đèn sáng, đặt lịch online tiện lợi. Giá hơi cao nhưng xứng đáng.", 8),
            (p4,  7, 4, "Sân sạch, nhân viên nhiệt tình. Mặt sàn vàng nhìn đẹp mắt.", 4),
            (p5,  8, 5, "Sân clay đúng chuẩn, có HLV hỗ trợ kỹ thuật. Rất xứng giá.", 2),
            (p6,  4, 5, "Sàn PVC êm, đèn sáng không chói, điều hòa mát. Hoàn hảo!", 2),
            (p6,  5, 4, "Chơi cầu lông ở đây rất sướng, không bị nắng hay mưa ảnh hưởng.", 9),
            (p7,  6, 4, "Sàn vinyl tốt, điều hòa inverter mát đều. Giá phải chăng.", 4),
            (p8, 7, 5, "Khu đôi rộng rãi, phù hợp nhóm 4 người. Phòng thay đồ sạch sẽ.", 1),
            ]
        for prod, u_idx, rating, content, days_ago in reviews_data:
            db.session.add(Review(
                product_id=prod.id,
                user_id=users[u_idx].id,
                rating=rating,
                content=content,
                created_at=datetime.now() - timedelta(days=days_ago)
            ))


        def seed_bills(users, products):
            for i in range(30):
                u = random.choice(users)
                p = random.choice(products)

                bill = Bill(
                    user_id=u.id,
                    product_id=p.id,
                    amount=p.price,
                    created_at=datetime.now() - timedelta(days=random.randint(0, 10))
                )
                db.session.add(bill)

            db.session.commit()
        seed_bills(users, all_products)
        print("✅ Seed xong! Tất cả dữ liệu đã được thêm thành công.")