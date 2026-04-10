from bookingapp import db, app
from bookingapp.models import (Category, Product, User, Booking,
                                Favorite, Amenity, TimeSlot, Review)
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
        cat_football   = Category(name="Sân bóng đá",    address="123 Nguyễn Văn Linh, Q7, TP.HCM",  phone="0909123456")
        cat_tennis     = Category(name="Sân tennis",      address="45 Lê Lợi, Q1, TP.HCM",            phone="0909988776")
        cat_pool       = Category(name="Hồ bơi",          address="88 Trần Hưng Đạo, Q5, TP.HCM",     phone="0911222333")
        cat_badminton  = Category(name="Sân cầu lông",    address="12 Lý Thường Kiệt, Q10, TP.HCM",   phone="0909333444")
        cat_basketball = Category(name="Sân bóng rổ",     address="99 Nguyễn Huệ, Q1, TP.HCM",        phone="0909555666")
        cat_volleyball = Category(name="Sân bóng chuyền", address="22 Hai Bà Trưng, Q3, TP.HCM",      phone="0909777888")
        cat_tabletennis= Category(name="Sân bóng bàn",    address="55 Nguyễn Trãi, Q5, TP.HCM",       phone="0909666777")
        cat_pickleball = Category(name="Sân pickleball",  address="77 Lê Văn Sỹ, Q3, TP.HCM",         phone="0909444555")

        db.session.add_all([cat_football, cat_tennis, cat_pool, cat_badminton,
                            cat_basketball, cat_volleyball, cat_tabletennis, cat_pickleball])
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

        # --- Hồ bơi ---
        p6 = Product(name="Hồ bơi 25m", price=200000, image="pool.jpg",
                     category_id=cat_pool.id,
                     description="Hồ bơi 25m x 12.5m, 6 đường bơi chuẩn FINA, hệ thống lọc nước ozone hiện đại, nhiệt độ nước 28-30°C quanh năm.")
        p7 = Product(name="Hồ bơi Olympic 50m", price=600000, image="pool.jpg",
                     category_id=cat_pool.id,
                     description="Hồ bơi Olympic 50m x 25m, 10 đường bơi chuẩn quốc tế, bảng điện tử tính giờ tự động, phù hợp cho vận động viên thi đấu chuyên nghiệp.")

        # --- Cầu lông ---
        p8 = Product(name="Sân cầu lông tiêu chuẩn 5 sao", price=150000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     description="Sân cầu lông sàn gỗ PVC chuyên dụng, đèn LED 1200 lux không chói mắt, điều hòa 2 chiều mát lạnh. Đạt chuẩn BWF cho thi đấu quốc tế.")
        p9 = Product(name="Sân cầu lông tiêu chuẩn hạng A", price=150000, image="caulong.jpg",
                     category_id=cat_badminton.id,
                     description="Sàn vinyl cao su chuyên dụng, hệ thống lưới căng chuẩn, điều hòa inverter tiết kiệm điện. Phù hợp luyện tập hàng ngày cho mọi trình độ.")
        p10 = Product(name="Sân cầu lông đôi", price=200000, image="caulong.jpg",
                      category_id=cat_badminton.id,
                      description="Khu sân cầu lông đôi ghép 2 sân, lý tưởng cho câu lạc bộ và nhóm bạn. Có phòng thay đồ riêng biệt cho nam và nữ.")

        # --- Bóng rổ ---
        p11 = Product(name="Sân bóng rổ ngoài trời A", price=250000, image="bongro.jpg",
                      category_id=cat_basketball.id,
                      description="Sân bóng rổ ngoài trời mặt nhựa FIBA, 2 trụ bóng rổ kính cường lực, hệ thống đèn pha cho chơi ban đêm. Sức chứa 200 người xem.")
        p12 = Product(name="Sân bóng rổ ngoài trời B", price=250000, image="bongro.jpg",
                      category_id=cat_basketball.id,
                      description="Sân bóng rổ nửa sân (half court) lý tưởng cho tập luyện 3v3, mặt sàn nhựa cao su chống trượt, khu vực nghỉ ngơi có mái che.")
        p13 = Product(name="Sân bóng rổ trong nhà", price=400000, image="bongro.jpg",
                      category_id=cat_basketball.id,
                      description="Sân bóng rổ trong nhà sàn gỗ maple chuẩn NBA, bảng điện tử tính điểm, điều hòa trung tâm, khán đài 300 ghế ngồi.")

        # --- Bóng chuyền ---
        p14 = Product(name="Sân bóng chuyền siêu rộng", price=180000, image="bongchuyen.jpg",
                      category_id=cat_volleyball.id,
                      description="Sân bóng chuyền trong nhà sàn gỗ chuẩn FIVB, lưới Mikasa chính hãng, hệ thống chiếu sáng đồng đều 800 lux trên toàn mặt sân.")
        p15 = Product(name="Sân bóng chuyền bãi biển", price=300000, image="bongchuyen.jpg",
                      category_id=cat_volleyball.id,
                      description="Sân bóng chuyền bãi biển nhân tạo với cát nhập khẩu mịn sạch, lưới chuyên dụng beach volleyball, phù hợp tổ chức giải đấu.")

        # --- Bóng bàn ---
        p16 = Product(name="Sân bóng bàn 2 bàn", price=120000, image="bongban.jpg",
                      category_id=cat_tabletennis.id,
                      description="2 bàn bóng bàn Butterfly chuyên nghiệp, sàn nhà yên tĩnh cách âm, điều hòa mát lạnh, cho thuê vợt và bóng tại chỗ.")
        p17 = Product(name="Sân bóng bàn 4 bàn", price=180000, image="bongban.jpg",
                      category_id=cat_tabletennis.id,
                      description="4 bàn bóng bàn STIGA cao cấp trong phòng rộng thoáng, đèn chuyên dụng không lóa mắt, phù hợp cho câu lạc bộ và giải đấu nhỏ.")

        # --- Pickleball ---
        p18 = Product(name="Sân pickleball hiện đại", price=200000, image="pickleball.jpg",
                      category_id=cat_pickleball.id,
                      description="Sân pickleball mặt sàn SportMaster chuyên dụng, lưới chuẩn USA Pickleball, đèn LED chiếu sáng đều, phòng chờ máy lạnh thoải mái.")
        p19 = Product(name="Sân pickleball tiêu chuẩn", price=250000, image="pickleball.jpg",
                      category_id=cat_pickleball.id,
                      description="Sân pickleball ngoài trời mái che, mặt sân acrylic chống trượt, cho thuê vợt và bóng, huấn luyện viên hỗ trợ cho người mới bắt đầu.")

        all_products = [p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,
                        p11,p12,p13,p14,p15,p16,p17,p18,p19]
        db.session.add_all(all_products)
        db.session.commit()

        # ===== AMENITIES =====
        amenities_map = {
            p1.id:  [("⚽","Cỏ nhân tạo FIFA"),("💡","Đèn LED 1000W"),("🚗","Gửi xe miễn phí"),("🚿","Phòng tắm nóng lạnh"),("☕","Căng tin & Cà phê")],
            p2.id:  [("⚽","Cỏ tự nhiên chuẩn FIFA"),("🏟","Khán đài 500 chỗ"),("🚗","Bãi đậu xe rộng"),("🚿","Phòng thay đồ VIP"),("🎙","Hệ thống loa"),("☕","Căng tin")],
            p3.id:  [("🎾","Mặt sân Plexicushion"),("💡","Chiếu sáng 800 lux"),("🚗","Gửi xe miễn phí"),("🚿","Phòng tắm"),("📶","Wifi tốc độ cao")],
            p4.id:  [("🎾","Mặt sân chống trượt"),("💡","Đèn ban đêm"),("🚗","Gửi xe miễn phí"),("🥤","Nước miễn phí"),("📶","Wifi")],
            p5.id:  [("🎾","Sân clay nhập khẩu"),("👨‍🏫","HLV hỗ trợ"),("🚗","Gửi xe VIP"),("🚿","Phòng thay đồ riêng"),("☕","Cafe miễn phí"),("📶","Wifi")],
            p6.id:  [("🏊","Hệ thống lọc ozone"),("🌡","Nước 28-30°C"),("🚿","Phòng tắm"),("🚗","Gửi xe"),("👨‍🏫","HLV dạy bơi"),("☕","Căng tin")],
            p7.id:  [("🏊","Chuẩn Olympic FINA"),("⏱","Bảng tính giờ tự động"),("🚿","Phòng thay đồ"),("🚗","Bãi xe rộng"),("🏥","Y tế trực chờ")],
            p8.id:  [("🏸","Sàn PVC chuẩn BWF"),("❄️","Điều hòa 2 chiều"),("💡","Đèn 1200 lux"),("🚗","Gửi xe miễn phí"),("🏸","Cho thuê vợt")],
            p9.id:  [("🏸","Sàn vinyl cao su"),("❄️","Điều hòa inverter"),("🚗","Gửi xe"),("🏸","Cho thuê vợt & cầu"),("📶","Wifi")],
            p10.id: [("🏸","Khu sân đôi"),("🚿","Phòng thay đồ riêng"),("❄️","Điều hòa"),("🚗","Gửi xe"),("☕","Căng tin")],
            p11.id: [("🏀","Mặt nhựa FIBA"),("💡","Đèn pha ban đêm"),("🚗","Gửi xe"),("🥤","Nước uống"),("📶","Wifi")],
            p12.id: [("🏀","Sân 3v3 half court"),("🛡","Mặt cao su chống trượt"),("🌂","Mái che"),("🚗","Gửi xe"),("☕","Căng tin")],
            p13.id: [("🏀","Sàn gỗ maple chuẩn NBA"),("❄️","Điều hòa trung tâm"),("🏟","Khán đài 300 ghế"),("📊","Bảng điện tử"),("🚿","Phòng thay đồ VIP")],
            p14.id: [("🏐","Sàn gỗ chuẩn FIVB"),("🏐","Lưới Mikasa"),("💡","Chiếu sáng 800 lux"),("🚗","Gửi xe"),("🚿","Phòng tắm")],
            p15.id: [("🏐","Cát nhập khẩu mịn sạch"),("🏐","Lưới beach volleyball"),("🌅","Không gian thoáng"),("🚗","Gửi xe"),("🥤","Nước miễn phí")],
            p16.id: [("🏓","Bàn Butterfly chuyên nghiệp"),("❄️","Điều hòa"),("🏓","Cho thuê vợt & bóng"),("🔇","Phòng cách âm"),("🚗","Gửi xe")],
            p17.id: [("🏓","4 bàn STIGA cao cấp"),("💡","Đèn chuyên dụng"),("❄️","Điều hòa"),("🏓","Cho thuê vợt"),("🚗","Gửi xe"),("☕","Căng tin")],
            p18.id: [("🎯","Mặt sân SportMaster"),("❄️","Phòng chờ máy lạnh"),("🎯","Lưới chuẩn USA Pickleball"),("🚗","Gửi xe"),("📶","Wifi")],
            p19.id: [("🎯","Mặt acrylic chống trượt"),("🌂","Mái che ngoài trời"),("👨‍🏫","HLV người mới"),("🎯","Cho thuê vợt & bóng"),("🚗","Gửi xe")],
        }
        for product_id, items in amenities_map.items():
            add_amenities(db.session.get(Product, product_id), items)

        # ===== TIME SLOTS =====
        for p in [p1, p2, p11, p12, p13, p14, p15]:
            add_slots(p, morning=True, afternoon=True, evening=True)
        for p in [p3, p4, p5]:
            add_slots(p, morning=True, afternoon=True, evening=False)
        for p in [p6, p7]:
            add_slots(p, morning=True, afternoon=True, evening=False)
        for p in [p8, p9, p10]:
            add_slots(p, morning=True, afternoon=True, evening=True)
        for p in [p16, p17, p18, p19]:
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
            (p6,  2, 5, "Nước trong vắt, hệ thống lọc ozone hiện đại. Nhiệt độ nước vừa phải.", 1),
            (p6,  9, 4, "Hồ bơi sạch, nhân viên cứu hộ chuyên nghiệp. Bãi giữ xe rộng.", 6),
            (p7,  3, 5, "Hồ Olympic chuẩn thật sự, thiết bị tính giờ hiện đại. Rất ấn tượng!", 3),
            (p8,  4, 5, "Sàn PVC êm, đèn sáng không chói, điều hòa mát. Hoàn hảo!", 2),
            (p8,  5, 4, "Chơi cầu lông ở đây rất sướng, không bị nắng hay mưa ảnh hưởng.", 9),
            (p9,  6, 4, "Sàn vinyl tốt, điều hòa inverter mát đều. Giá phải chăng.", 4),
            (p10, 7, 5, "Khu đôi rộng rãi, phù hợp nhóm 4 người. Phòng thay đồ sạch sẽ.", 1),
            (p11, 8, 4, "Sân bóng rổ ngoài trời đẹp, đèn pha đủ sáng ban đêm.", 5),
            (p12, 9, 5, "Half court cực kỳ phù hợp cho 3v3, mặt cao su không trượt.", 3),
            (p13, 1, 5, "Sân trong nhà chuẩn NBA luôn! Sàn gỗ maple rất êm, khán đài đẹp.", 2),
            (p14, 2, 4, "Sân bóng chuyền rộng, lưới Mikasa chuẩn, ánh đèn đồng đều.", 6),
            (p15, 3, 5, "Cát mịn sạch, không có đá hay dị vật. Chơi rất thoải mái!", 1),
            (p16, 4, 4, "Bàn Butterfly chất lượng, phòng yên tĩnh. Cho thuê vợt giá tốt.", 4),
            (p17, 5, 5, "4 bàn STIGA xịn, đèn chuyên dụng không lóa mắt. Rất chuyên nghiệp.", 2),
            (p18, 6, 5, "Mặt sân SportMaster đúng chuẩn, phòng chờ mát mẻ. Rất thích!", 3),
            (p19, 7, 4, "Sân ngoài trời có mái che tiện lợi, HLV tận tình với người mới.", 5),
        ]
        for prod, u_idx, rating, content, days_ago in reviews_data:
            db.session.add(Review(
                product_id=prod.id,
                user_id=users[u_idx].id,
                rating=rating,
                content=content,
                created_at=datetime.now() - timedelta(days=days_ago)
            ))
        db.session.commit()

        # ===== FAVORITES =====
        fav_pairs = set()
        for _ in range(30):
            u = random.choice(users)
            p = random.choice(all_products)
            if (u.id, p.id) not in fav_pairs:
                fav_pairs.add((u.id, p.id))
                db.session.add(Favorite(user_id=u.id, product_id=p.id))
        db.session.commit()

        print("✅ Seed xong! Tất cả dữ liệu đã được thêm thành công.")