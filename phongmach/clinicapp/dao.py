from clinicapp.models import (User, UserRole, QuyDinh, DonViThuoc, Thuoc,
                              BenhNhan, DanhSachKham, PhieuKham, ChiTietToaThuoc, HoaDon)
from clinicapp import db
from sqlalchemy import func, extract
from twilio.rest import Client
import hashlib


def get_user_by_id(user_id):
    return User.query.get(user_id)


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


def get_quy_dinh():
    qd = QuyDinh.query.first()
    if not qd:
        qd = QuyDinh(so_benh_nhan_toi_da=40, tien_kham=100000)
        db.session.add(qd)
        db.session.commit()
    return qd


def load_danh_sach_kham(ngay_kham, trang_thai=None):
    query = DanhSachKham.query.filter(DanhSachKham.ngay_kham.__eq__(ngay_kham))
    if trang_thai:
        query = query.filter(DanhSachKham.trang_thai.__eq__(trang_thai))
    return query.all()


def load_thuocs(kw=None):
    query = Thuoc.query
    if kw:
        query = query.filter(Thuoc.ten_thuoc.contains(kw))
    return query.all()


def send_sms_twilio(phone, message):
    # Cấu hình Twilio API của bạn tại đây
    ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    FROM_PHONE = "+1234567890"
    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        to_phone = "+84" + phone[1:] if phone.startswith("0") else phone
        client.messages.create(body=message, from_=FROM_PHONE, to=to_phone)
        return True
    except Exception as ex:
        print(f"Twilio SMS Log (chưa cấu hình key thật): {ex}")
        return False


def stats_revenue_by_month(month, year):
    return db.session.query(
        HoaDon.ngay_thanh_toan,
        func.count(HoaDon.id),
        func.sum(HoaDon.tong_tien)
    ).filter(
        extract('month', HoaDon.ngay_thanh_toan) == month,
        extract('year', HoaDon.ngay_thanh_toan) == year
    ).group_by(HoaDon.ngay_thanh_toan).all()


def stats_medicine_by_month(month, year):
    return db.session.query(
        Thuoc.ten_thuoc,
        DonViThuoc.ten_don_vi,
        func.sum(ChiTietToaThuoc.so_luong),
        func.count(ChiTietToaThuoc.id)
    ).join(DonViThuoc, Thuoc.don_vi_id.__eq__(DonViThuoc.id))\
     .join(ChiTietToaThuoc, ChiTietToaThuoc.thuoc_id.__eq__(Thuoc.id))\
     .join(PhieuKham, ChiTietToaThuoc.phieu_kham_id.__eq__(PhieuKham.id))\
     .filter(
        extract('month', PhieuKham.ngay_kham) == month,
        extract('year', PhieuKham.ngay_kham) == year
    ).group_by(Thuoc.id, DonViThuoc.ten_don_vi).all()