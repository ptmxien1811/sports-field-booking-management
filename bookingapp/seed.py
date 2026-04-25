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
        db.drop_all()
        db.create_all()

        # ===== CATEGORIES =====
        cat_football   = Category(id=1, name="Sân bóng đá")
        cat_tennis     = Category(id=2, name="Sân tennis")
        cat_badminton  = Category(id=3, name="Sân cầu lông")

        db.session.add_all([cat_football, cat_tennis, cat_badminton])
        db.session.commit()

        # ===== PRODUCTS - BÓNG ĐÁ =====
        p1 = Product(name="Sân bóng đá mini 7 người", price=500000, image="football.jpg",
                     category_id=cat_football.id,
                     address="123 Nguyễn Văn Linh, Quận 7, TP.HCM",
                     phone="0901234567",
                     description="Sân cỏ nhân tạo thế hệ mới FIFA Quality Pro, đèn LED 1000W, hệ thống tưới tự động.")
        p2 = Product(name="Sân bóng đá 11 người", price=800000, image="football.jpg",
                     category_id=cat_football.id,
                     address="45 Lê Văn Việt, Quận 9, TP.HCM",
                     phone="0912345678",
                     description="Sân cỏ tự nhiên chuẩn FIFA, kích thước 100x68m, hệ thống thoát nước tốt, khán đài 500 chỗ ngồi.")
        p3_fb = Product(name="Sân bóng đá 5 người Phú Mỹ Hưng", price=350000, image="football.jpg",
                     category_id=cat_football.id,
                     address="78 Nguyễn Lương Bằng, Phú Mỹ Hưng, Quận 7, TP.HCM",
                     phone="0923456789",
                     description="Sân cỏ nhân tạo 5 người, có mái che, phù hợp thi đấu mọi thời tiết.")
        p4_fb = Product(name="Sân bóng đá Thủ Đức", price=450000, image="football.jpg",
                     category_id=cat_football.id,
                     address="200 Võ Văn Ngân, TP. Thủ Đức, TP.HCM",
                     phone="0934567890",
                     description="Sân cỏ nhân tạo thế hệ mới, đèn LED sáng rõ, phù hợp cho các trận đấu buổi tối.")
        p5_fb = Product(name="Sân bóng đá Bình Thạnh", price=400000, image="football.jpg",
                     category_id=cat_football.id,
                     address="56 Bạch Đằng, Quận Bình Thạnh, TP.HCM",
                     phone="0945678901",
                     description="Sân bóng đá mini tiêu chuẩn, có hệ thống camera an ninh, bãi xe rộng rãi.")

        # ===== PRODUCTS - TENNIS =====
        p6_tn = Product(name="Sân tennis tiêu chuẩn màu xanh", price=300000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     address="12 Trần Hưng Đạo, Quận 1, TP.HCM",
                     phone="0956789012",
                     description="Mặt sân Plexicushion xanh chuẩn ATP, hệ thống chiếu sáng 800 lux.")
        p7_tn = Product(name="Sân tennis tiêu chuẩn màu vàng", price=300000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     address="34 Đinh Tiên Hoàng, Quận Bình Thạnh, TP.HCM",
                     phone="0967890123",
                     description="Mặt sân Plexicushion vàng chống trượt, hệ thống lưới căng tự động.")
        p8_tn = Product(name="Sân tennis cao cấp VIP", price=500000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     address="89 Lê Duẩn, Quận 1, TP.HCM",
                     phone="0978901234",
                     description="Sân tennis VIP mặt sân đất nện (clay) nhập khẩu từ Châu Âu, phòng thay đồ riêng.")
        p9_tn = Product(name="Sân tennis Phú Nhuận", price=280000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     address="15 Phan Đình Phùng, Quận Phú Nhuận, TP.HCM",
                     phone="0989012345",
                     description="Sân tennis tiêu chuẩn, mái che toàn bộ, phù hợp chơi mọi thời tiết.")
        p10_tn = Product(name="Sân tennis Quận 3", price=320000, image="tennis.jpg",
                     category_id=cat_tennis.id,
                     address="67 Võ Văn Tần, Quận 3, TP.HCM",
                     phone="0990123456",
                     description="Sân tennis hiện đại, có HLV hỗ trợ theo yêu cầu, cho thuê vợt và bóng.")

        # ===== PRODUCTS - CẦU LÔNG =====
        p11_cl = Product(name="Sân cầu lông tiêu chuẩn 5 sao", price=150000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     address="90 Cách Mạng Tháng 8, Quận 3, TP.HCM",
                     phone="0901122334",
                     description="Sàn PVC chuyên dụng, đèn LED 1200 lux không chói mắt, điều hòa 2 chiều. Đạt chuẩn BWF.")
        p12_cl = Product(name="Sân cầu lông tiêu chuẩn hạng A", price=150000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     address="23 Lý Thường Kiệt, Quận 10, TP.HCM",
                     phone="0912233445",
                     description="Sàn vinyl cao su chuyên dụng, điều hòa inverter tiết kiệm điện.")
        p13_cl = Product(name="Sân cầu lông đôi Gò Vấp", price=200000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     address="112 Quang Trung, Quận Gò Vấp, TP.HCM",
                     phone="0923344556",
                     description="Khu sân đôi ghép 2 sân, lý tưởng cho câu lạc bộ và nhóm bạn.")
        p14_cl = Product(name="Sân cầu lông Tân Bình", price=130000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     address="45 Hoàng Văn Thụ, Quận Tân Bình, TP.HCM",
                     phone="0934455667",
                     description="Sân cầu lông giá rẻ, thoáng mát, phù hợp luyện tập hàng ngày.")
        p15_cl = Product(name="Sân cầu lông Bình Dương", price=120000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     address="78 Đại lộ Bình Dương, TP. Thủ Dầu Một, Bình Dương",
                     phone="0945566778",
                     description="Sân cầu lông mới khai trương, sàn gỗ tự nhiên, điều hòa mát lạnh.")

        all_products = [p1,p2,p3_fb,p4_fb,p5_fb,
                        p6_tn,p7_tn,p8_tn,p9_tn,p10_tn,
                        p11_cl,p12_cl,p13_cl,p14_cl,p15_cl]
        db.session.add_all(all_products)
        db.session.commit()

        # ===== AMENITIES =====
        amenities_map = {
            p1.id:     [("⚽","Cỏ nhân tạo FIFA"),("💡","Đèn LED 1000W"),("🚗","Gửi xe miễn phí"),("🚿","Phòng tắm nóng lạnh"),("☕","Căng tin & Cà phê")],
            p2.id:     [("⚽","Cỏ tự nhiên chuẩn FIFA"),("🏟","Khán đài 500 chỗ"),("🚗","Bãi đậu xe rộng"),("🚿","Phòng thay đồ VIP"),("☕","Căng tin")],
            p3_fb.id:  [("⚽","Cỏ nhân tạo"),("🌂","Mái che toàn bộ"),("🚗","Gửi xe miễn phí"),("💡","Đèn LED"),("🚿","Phòng tắm")],
            p4_fb.id:  [("⚽","Cỏ nhân tạo"),("💡","Đèn LED sáng"),("🚗","Gửi xe"),("📶","Wifi"),("☕","Căng tin")],
            p5_fb.id:  [("⚽","Sân cỏ chuẩn"),("📹","Camera an ninh"),("🚗","Bãi xe rộng"),("🚿","Phòng thay đồ"),("☕","Căng tin")],
            p6_tn.id:  [("🎾","Mặt sân Plexicushion"),("💡","Chiếu sáng 800 lux"),("🚗","Gửi xe miễn phí"),("🚿","Phòng tắm"),("📶","Wifi tốc độ cao")],
            p7_tn.id:  [("🎾","Mặt sân chống trượt"),("💡","Đèn ban đêm"),("🚗","Gửi xe miễn phí"),("🥤","Nước miễn phí"),("📶","Wifi")],
            p8_tn.id:  [("🎾","Sân clay nhập khẩu"),("👨‍🏫","HLV hỗ trợ"),("🚗","Gửi xe VIP"),("🚿","Phòng thay đồ riêng"),("☕","Cafe miễn phí"),("📶","Wifi")],
            p9_tn.id:  [("🎾","Mái che toàn bộ"),("💡","Đèn LED"),("🚗","Gửi xe"),("🥤","Nước uống"),("📶","Wifi")],
            p10_tn.id: [("🎾","Mặt sân hiện đại"),("👨‍🏫","HLV theo yêu cầu"),("🏸","Cho thuê vợt"),("🚗","Gửi xe"),("☕","Căng tin")],
            p11_cl.id: [("🏸","Sàn PVC chuẩn BWF"),("❄️","Điều hòa 2 chiều"),("💡","Đèn 1200 lux"),("🚗","Gửi xe miễn phí"),("🏸","Cho thuê vợt")],
            p12_cl.id: [("🏸","Sàn vinyl cao su"),("❄️","Điều hòa inverter"),("🚗","Gửi xe"),("🏸","Cho thuê vợt & cầu"),("📶","Wifi")],
            p13_cl.id: [("🏸","Khu sân đôi"),("🚿","Phòng thay đồ riêng"),("❄️","Điều hòa"),("🚗","Gửi xe"),("☕","Căng tin")],
            p14_cl.id: [("🏸","Sân thoáng mát"),("💡","Đèn LED"),("🚗","Gửi xe"),("🥤","Nước uống"),("🏸","Cho thuê vợt")],
            p15_cl.id: [("🏸","Sàn gỗ tự nhiên"),("❄️","Điều hòa mát lạnh"),("🚗","Gửi xe miễn phí"),("📶","Wifi"),("☕","Căng tin")],
        }
        for product_id, items in amenities_map.items():
            add_amenities(db.session.get(Product, product_id), items)

        # ===== TIME SLOTS =====
        for p in [p1, p2, p3_fb, p4_fb, p5_fb]:
            add_slots(p, morning=True, afternoon=True, evening=True)
        for p in [p6_tn, p7_tn, p8_tn, p9_tn, p10_tn]:
            add_slots(p, morning=True, afternoon=True, evening=False)
        for p in [p11_cl, p12_cl, p13_cl, p14_cl, p15_cl]:
            add_slots(p, morning=True, afternoon=True, evening=True)

        db.session.commit()

        # ===== USERS =====
        users_data = [
            ("admin",              "Admin@123!"),
            ("Phạm Thị Mỹ Xuyên", "Xuyen@123!"),
            ("Lý Đại Long",        "Long@123!"),
            ("Ngô Thị Thúy Quyên","Quyen@123!"),
            ("Nguyễn Văn Kiên",    "Kien@123!"),
            ("Trần Thị Tú",        "Tu@1234!"),
            ("Lê Văn Kha",         "Kha@1234!"),
            ("Hoàng Thị Diệu",     "Dieu@123!"),
            ("Phạm Văn Anh",       "Anh@1234!"),
            ("Đỗ Thị Hòa",         "Hoa@1234!"),
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
            (p1,      1, 5, "Sân cỏ rất đẹp, mịn mượt, đèn sáng rõ. Nhân viên thân thiện!", 2),
            (p1,      2, 4, "Giá hợp lý, bãi xe rộng. Cỏ hơi cứng một chút nhưng chơi được.", 5),
            (p2,      3, 5, "Sân 11 người chuẩn quá, cỏ tự nhiên xanh mướt, rất chuyên nghiệp.", 1),
            (p3_fb,   4, 4, "Có mái che rất tiện, không sợ mưa nắng.", 3),
            (p4_fb,   5, 5, "Đèn LED sáng rõ, đặt tối vẫn chơi tốt. Giá hợp lý.", 7),
            (p6_tn,   1, 5, "Mặt sân Plexicushion cực kỳ tốt, không trượt, bóng nảy đều.", 3),
            (p7_tn,   6, 4, "Đèn sáng, đặt lịch online tiện lợi.", 8),
            (p8_tn,   7, 5, "Sân clay đúng chuẩn, có HLV hỗ trợ kỹ thuật.", 2),
            (p9_tn,   8, 4, "Mái che tiện, không bị nắng. Sẽ quay lại.", 4),
            (p11_cl,  4, 5, "Sàn PVC êm, đèn sáng không chói, điều hòa mát. Hoàn hảo!", 2),
            (p12_cl,  5, 4, "Chơi cầu lông ở đây rất sướng, điều hòa mát đều.", 9),
            (p13_cl,  6, 5, "Khu đôi rộng rãi, phù hợp nhóm 4 người.", 1),
            (p14_cl,  7, 4, "Giá rẻ, thoáng mát, phù hợp luyện tập hàng ngày.", 5),
            (p15_cl,  8, 5, "Sàn gỗ tự nhiên cực đẹp, điều hòa mát lạnh.", 3),
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
            methods = ['direct', 'online']
            for i in range(40):
                u = random.choice(users)
                p = random.choice(products)
                bill = Bill(
                    user_id=u.id,
                    product_id=p.id,
                    booking_id=None,
                    amount=p.price,
                    payment_method=random.choice(methods),
                    created_at=datetime.now() - timedelta(days=random.randint(0, 15))
                )
                db.session.add(bill)
            db.session.commit()

        seed_bills(users, all_products)
        db.session.commit()
        print("✅ Seed xong! Tất cả dữ liệu đã được thêm thành công.")