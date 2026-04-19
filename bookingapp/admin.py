from flask import session, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from bookingapp import app, db
from bookingapp.models import Category, Product, User, TimeSlot, Booking, Bill
from datetime import datetime
from sqlalchemy import func
from flask_admin.form import ImageUploadField
import os
from flask_admin.model import InlineFormAdmin
from wtforms import SelectField

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not (session.get("username") and session.get("username").lower() == "admin"):
            flash("Bạn không có quyền truy cập!", "danger")
            return redirect(url_for("login"))
        total_revenue = db.session.query(func.sum(Bill.amount)).scalar()
        stats = {
            # Đếm tổng số lượng từ các Model đã có
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
            'total_products': Product.query.count(),
            'total_bookings': db.session.query(func.count(Bill.id)).scalar(),
            'total_revenue': total_revenue
        }
        return self.render('home-admin.html', stats=stats)

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
    column_searchable_list = ['id','name']
    column_filters = ['id','name']
    form_columns = ['id', 'name']
    column_labels = {
        'name': 'Tên loại sân',
        'product': 'Danh sách sân'
    }

TIME_SLOTS = [
    ("06:00 - 07:00", "06:00 - 07:00"),
    ("07:00 - 08:00", "07:00 - 08:00"),
    ("08:00 - 09:00", "08:00 - 09:00"),
    ("09:00 - 10:00", "09:00 - 10:00"),
    ("10:00 - 11:00", "10:00 - 11:00"),
    ("11:00 - 12:00", "11:00 - 12:00"),

    ("13:00 - 14:00", "13:00 - 14:00"),
    ("14:00 - 15:00", "14:00 - 15:00"),
    ("15:00 - 16:00", "15:00 - 16:00"),
    ("16:00 - 17:00", "16:00 - 17:00"),
    ("17:00 - 18:00", "17:00 - 18:00"),
    ("18:00 - 19:00", "18:00 - 19:00"),

    ("19:00 - 20:00", "19:00 - 20:00"),
    ("20:00 - 21:00", "20:00 - 21:00"),
    ("21:00 - 22:00", "21:00 - 22:00"),
]

class TimeSlotInlineModel(InlineFormAdmin):
    form_extra_fields = {
        'label': SelectField('Khung giờ', choices=TIME_SLOTS)
    }

    def on_model_change(self, form, model, is_created):
        label = model.label

        # Auto set period
        hour = int(label.split(":")[0])

        if 6 <= hour < 12:
            model.period = "morning"
        elif 13 <= hour < 19:
            model.period = "afternoon"
        else:
            model.period = "evening"
inline_models = [TimeSlotInlineModel(TimeSlot)]

class ProductView(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['name', 'price']
    column_filters = ['name', 'price']
    column_labels = {
        'name': 'Tên Sân',
        'price': 'Giá',
        'address': 'Địa Chỉ',
        'phone':'SĐT',
        'image': 'Ảnh',
        'active': 'Hoạt động',
        'created_at': 'Ngày tạo',
        'category': 'Loại sân'
    }
    column_sortable_list = ['id','name', 'price']
    form_excluded_columns = ['bookings', 'favorites', 'amenities']
    form_extra_fields = {
        'image': ImageUploadField(
            'Ảnh',
            base_path=os.path.join(os.path.dirname(__file__), 'static/images'),
            relative_path='uploads/',
            namegen=lambda obj, file_data: file_data.filename
        )
    }

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