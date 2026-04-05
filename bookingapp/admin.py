from flask import session, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from bookingapp import app, db
from bookingapp.models import Category, Product, User

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not (session.get("username") and session.get("username").lower() == "admin"):
            flash("Bạn không có quyền truy cập!", "danger")
            return redirect(url_for("login"))

        return self.render('admin/home-admin.html')

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
    column_labels = {
        'name': 'Tên loại sân',
        'product': 'Danh sách sân'
    }

class ProductView(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['name', 'price','address','phone']
    column_filters = ['name', 'price','address','phone']
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

# Đăng ký tất cả view với SecureModelView
admin.add_view(CategoryView(Category, db.session))
admin.add_view(ProductView(Product, db.session))
admin.add_view(SecureModelView(User, db.session))
