# admin.py - HOÀN CHỈNH

from flask import session, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import ImageUploadField
from flask_admin.model import InlineFormAdmin
from wtforms import SelectField
from sqlalchemy import func
from datetime import datetime
import os


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not (session.get("username") and session.get("username").lower() == "admin"):
            flash("Bạn không có quyền truy cập!", "danger")
            return redirect(url_for("login"))

        # Import lazy để tránh circular import
        from bookingapp import db
        from bookingapp.models import User, Category, Product, Bill

        total_revenue = db.session.query(func.sum(Bill.amount)).scalar()
        stats = {
            'total_users':      User.query.count(),
            'total_categories': Category.query.count(),
            'total_products':   Product.query.count(),
            'total_bookings':   db.session.query(func.count(Bill.id)).scalar(),
            'total_revenue':    total_revenue,
        }
        return self.render('home-admin.html', stats=stats)


class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get("username") and session.get("username").lower() == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("login"))


class CategoryView(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['id', 'name']
    column_filters = ['id', 'name']
    form_columns = ['id', 'name']
    column_labels = {
        'name':    'Tên loại sân',
        'product': 'Danh sách sân',
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
        hour = int(label.split(":")[0])
        if 6 <= hour < 12:
            model.period = "morning"
        elif 13 <= hour < 19:
            model.period = "afternoon"
        else:
            model.period = "evening"


class ProductView(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['name', 'price']
    column_filters = ['name', 'price']
    column_labels = {
        'name':       'Tên Sân',
        'price':      'Giá',
        'address':    'Địa Chỉ',
        'phone':      'SĐT',
        'image':      'Ảnh',
        'active':     'Hoạt động',
        'created_at': 'Ngày tạo',
        'category':   'Loại sân',
    }
    column_sortable_list = ['id', 'name', 'price']
    form_excluded_columns = ['bookings', 'favorites', 'amenities', 'reviews']
    form_extra_fields = {
        'image': ImageUploadField(
            'Ảnh',
            base_path=os.path.join(os.path.dirname(__file__), 'static/images'),
            relative_path='uploads/',
            namegen=lambda obj, file_data: file_data.filename,
        )
    }

    def on_model_delete(self, model):
        from bookingapp.models import Booking
        now = datetime.now()
        future_booking = Booking.query.filter(
            Booking.product_id == model.id,
            Booking.date >= now,
            Booking.status == 'confirmed'
        ).first()

        if future_booking:
            flash(
                f"Sân này đang có lịch đặt vào ngày "
                f"{future_booking.date.strftime('%d/%m/%Y')}. Không thể xóa!",
                "danger"
            )
            return True   # truthy → chặn xóa
        return None       # falsy → cho phép xóa

    def delete_model(self, model):
        try:
            result = self.on_model_delete(model)
            if result:
                return False
            self.session.delete(model)
            self.session.commit()
            return True
        except Exception as ex:
            flash(str(ex), 'error')
            self.session.rollback()
            return False


class BillView(SecureModelView):
    can_view_details = True
    can_create  = False
    can_edit    = False
    can_delete  = True
    can_export  = True
    column_list = ['id', 'user', 'product', 'booking_id',
                   'amount', 'payment_method', 'created_at']
    column_searchable_list = ['id', 'payment_method']
    column_filters         = ['id', 'amount', 'payment_method', 'created_at']
    column_sortable_list   = ['id', 'amount', 'created_at']
    column_labels = {
        'id':             'Mã HĐ',
        'user':           'Người dùng',
        'product':        'Sân',
        'booking_id':     'Mã đặt sân',
        'amount':         'Số tiền',
        'payment_method': 'Phương thức TT',
        'created_at':     'Ngày tạo',
    }


def init_admin(app, db):
    """
    Gọi hàm này từ __init__.py sau khi app + db sẵn sàng.
    Tất cả binding Admin → app xảy ra ở đây, không phải lúc import.
    """
    from bookingapp.models import Category, Product, Bill, TimeSlot

    admin_obj = Admin(
        app=app,
        name='Administrator',
        index_view=MyAdminIndexView(),
    )
    app.config.setdefault('FLASK_ADMIN_SWATCH', 'lux')
    app.secret_key = app.secret_key or '@#$%%^^&&&*^%$##@@#^^&&B GVFCDXDVHNJHFCV()(*&^'

    admin_obj.add_view(CategoryView(Category, db.session))
    admin_obj.add_view(
        ProductView(
            Product, db.session,
        )
    )
    admin_obj.add_view(BillView(Bill, db.session, name='Bill'))

    return admin_obj