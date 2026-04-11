from flask import session, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from bookingapp import app, db
from bookingapp.models import Category, Product, User
from datetime import datetime
from bookingapp.models import Booking
from sqlalchemy import func

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not (session.get("username") and session.get("username").lower() == "admin"):
            flash("Bạn không có quyền truy cập!", "danger")
            return redirect(url_for("login"))
        stats = {
            # Đếm tổng số lượng từ các Model đã có
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
            'total_products': Product.query.count(),
            'total_bookings': Booking.query.count(),
            'total_revenue': db.session.query(func.sum(Product.price)) \
                                 .join(Booking) \
                                 .filter(Booking.status == 'confirmed') \
                                 .scalar() or 0
        }
        return self.render('admin/home-admin.html', stats=stats)

admin = Admin(
    app=app,
    name='Administrator',
    index_view=MyAdminIndexView()
)
app.secret_key = '@#$%%^^&&&*^%$##@@#^^&&B GVFCDXDVHNJHFCV()(*&^'
app.config['FLASK_ADMIN_SWATCH'] = 'lux'

# View chung có kiểm tra quyền
class SecureModelView(ModelView):
    def is_accessible(self):
        # chỉ cho phép admin đăng nhập mới vào
        return session.get("username") and session.get("username").lower() == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("login"))

class CategoryView(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['name', 'address', 'phone']
    column_filters = ['name', 'address', 'phone']
    column_labels = {
        'name': 'Tên loại sân',
        'address': 'Địa chỉ',
        'phone': 'Số điện thoại',
        'product': 'Danh sách sân'
    }

class ProductView(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['name', 'price']
    column_filters = ['name', 'price']
    column_labels = {
        'name': 'Tên Sân',
        'price': 'Giá',
        'image': 'Ảnh',
        'active': 'Hoạt động',
        'created_at': 'Ngày tạo',
        'category': 'Loại sân'
    }
    column_sortable_list = ['id','name', 'price']

    def on_model_delete(self, model):
        now = datetime.now()

        future_booking = Booking.query.filter(
            Booking.product_id == model.id,
            Booking.date >= now,
            Booking.status == 'confirmed'
        ).first()

        if future_booking:
            flash(
                f"Sân này đang có lịch đặt vào ngày {future_booking.date.strftime('%d/%m/%Y')}. ",
                "danger"
            )
            return redirect(url_for('.index_view'))
    def delete_model(self, model):
        try:
            res = self.on_model_delete(model)
            if res:
                return False

            self.session.delete(model)
            self.session.commit()
            return True
        except Exception as ex:
            flash(str(ex), 'error')
            self.session.rollback()
            return False

# Đăng ký tất cả view với SecureModelView
admin.add_view(CategoryView(Category, db.session))
admin.add_view(ProductView(Product, db.session))
admin.add_view(SecureModelView(User, db.session))