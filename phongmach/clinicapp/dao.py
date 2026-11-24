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


def stats_revenue_by_time(year=None, time='month'):
    if time == 'quarter':
        time_col = func.ceil(extract('month', HoaDon.ngay_thanh_toan) / 3.0).label('time_unit')
    else:
        time_col = extract(time, HoaDon.ngay_thanh_toan).label('time_unit')

    query = db.session.query(
        time_col,
        func.count(HoaDon.id),
        func.sum(HoaDon.tong_tien)
    )

    if year:
        query = query.filter(extract('year', HoaDon.ngay_thanh_toan) == int(year))

    return query.group_by(time_col).order_by(time_col).all()


def stats_medicine_usage(kw=None, year=None, time='month'):
    query = db.session.query(
        Thuoc.ten_thuoc,
        DonViThuoc.ten_don_vi,
        func.sum(ChiTietToaThuoc.so_luong),
        func.count(ChiTietToaThuoc.id)
    ).join(DonViThuoc, Thuoc.don_vi_id.__eq__(DonViThuoc.id))\
     .join(ChiTietToaThuoc, ChiTietToaThuoc.thuoc_id.__eq__(Thuoc.id))\
     .join(PhieuKham, ChiTietToaThuoc.phieu_kham_id.__eq__(PhieuKham.id))

    if kw:
        query = query.filter(Thuoc.ten_thuoc.contains(kw.strip()))

    if year:
        query = query.filter(extract('year', PhieuKham.ngay_kham) == int(year))

    return query.group_by(Thuoc.id, Thuoc.ten_thuoc, DonViThuoc.ten_don_vi).all()


def create_user(name, username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name.strip(),
             username=username.strip(),
             password=password,
             user_role=UserRole.PATIENT)
    db.session.add(u)
    db.session.commit()


def get_or_create_benh_nhan(ho_ten, gioi_tinh, nam_sinh, dia_chi, so_dien_thoai):
    sdt = so_dien_thoai.strip()
    bn = BenhNhan.query.filter(BenhNhan.so_dien_thoai == sdt).first()
    if bn:
        bn.ho_ten = ho_ten.strip()
        bn.gioi_tinh = gioi_tinh
        bn.nam_sinh = int(nam_sinh)
        bn.dia_chi = dia_chi.strip()
    else:
        bn = BenhNhan(
            ho_ten=ho_ten.strip(),
            gioi_tinh=gioi_tinh,
            nam_sinh=int(nam_sinh),
            dia_chi=dia_chi.strip(),
            so_dien_thoai=sdt
        )
        db.session.add(bn)
    db.session.flush()
    return bn


def load_ho_so_benh_an(kw=None):
    query = BenhNhan.query.filter(BenhNhan.phieu_khams.any())
    if kw:
        kw = kw.strip()
        query = query.filter(
            (BenhNhan.ho_ten.contains(kw)) | (BenhNhan.so_dien_thoai.contains(kw))
        )
    return query.all()