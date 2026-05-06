# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/bookingapp?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'super_secret_key'

db = SQLAlchemy()   # ← KHÔNG truyền app
db.init_app(app)    # ← init ngay sau

# Khởi tạo Admin (bind vào app thật)
from bookingapp.admin import init_admin
init_admin(app, db)