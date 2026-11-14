from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from clinicapp import db, app
from flask_login import UserMixin
from enum import Enum as RoleEnum
from datetime import datetime, date
import hashlib


class UserRole(RoleEnum):
    ADMIN = 1
    NURSE = 2     # Y tá
    DOCTOR = 3    # Bác sĩ
    CASHIER = 4   # Thu ngân


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class User(BaseModel, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    avatar = Column(String(100), default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1688179242/hclq65mc6so7vdrbp7hz.jpg')
    user_role = Column(Enum(UserRole), default=UserRole.NURSE)
    phieu_khams = relationship('PhieuKham', backref='bac_si', lazy=True)

    def __str__(self):
        return self.name


class QuyDinh(BaseModel):
    so_benh_nhan_toi_da = Column(Integer, default=40)
    tien_kham = Column(Float, default=100000)


class DonViThuoc(BaseModel):
    ten_don_vi = Column(String(50), nullable=False, unique=True)  # viên, chai, vĩ
    thuocs = relationship('Thuoc', backref='don_vi', lazy=True)

    def __str__(self):
        return self.ten_don_vi


class Thuoc(BaseModel):
    ten_thuoc = Column(String(100), nullable=False)
    don_gia = Column(Float, default=0)
    don_vi_id = Column(Integer, ForeignKey(DonViThuoc.id), nullable=False)
    chi_tiet_toas = relationship('ChiTietToaThuoc', backref='thuoc', lazy=True)

    def __str__(self):
        return f"{self.ten_thuoc} ({self.don_vi.ten_don_vi})"


class BenhNhan(BaseModel):
    ho_ten = Column(String(100), nullable=False)
    gioi_tinh = Column(String(10), nullable=False)
    nam_sinh = Column(Integer, nullable=False)
    dia_chi = Column(String(200), nullable=False)
    so_dien_thoai = Column(String(15), nullable=False)
    danh_sach_khams = relationship('DanhSachKham', backref='benh_nhan', lazy=True)
    phieu_khams = relationship('PhieuKham', backref='benh_nhan', lazy=True)

    def __str__(self):
        return self.ho_ten


class DanhSachKham(BaseModel):
    ngay_kham = Column(Date, default=date.today, nullable=False)
    trang_thai = Column(String(50), default='Chờ khám')
    benh_nhan_id = Column(Integer, ForeignKey(BenhNhan.id), nullable=False)


class PhieuKham(BaseModel):
    ngay_kham = Column(Date, default=date.today, nullable=False)
    trieu_chung = Column(Text, nullable=False)
    du_doan_benh = Column(String(200), nullable=False)
    benh_nhan_id = Column(Integer, ForeignKey(BenhNhan.id), nullable=False)
    bac_si_id = Column(Integer, ForeignKey(User.id), nullable=True)
    chi_tiet_toas = relationship('ChiTietToaThuoc', backref='phieu_kham', lazy=True)
    hoa_don = relationship('HoaDon', backref='phieu_kham', uselist=False)


class ChiTietToaThuoc(BaseModel):
    phieu_kham_id = Column(Integer, ForeignKey(PhieuKham.id), nullable=False)
    thuoc_id = Column(Integer, ForeignKey(Thuoc.id), nullable=False)
    so_luong = Column(Integer, default=1)
    cach_dung = Column(String(200), nullable=False)


class HoaDon(BaseModel):
    phieu_kham_id = Column(Integer, ForeignKey(PhieuKham.id), nullable=False)
    ngay_thanh_toan = Column(Date, default=date.today, nullable=False)
    tien_kham = Column(Float, nullable=False)
    tien_thuoc = Column(Float, nullable=False)
    tong_tien = Column(Float, nullable=False)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Tạo tài khoản mẫu cho các vai trò (mật khẩu đều là: 123456)
        pw = str(hashlib.md5('123456'.encode('utf-8')).hexdigest())
        if not User.query.first():
            u1 = User(name='Quản Trị Viên', username='admin', password=pw, user_role=UserRole.ADMIN)
            u2 = User(name='Y Tá Lan', username='yta', password=pw, user_role=UserRole.NURSE)
            u3 = User(name='Bác Sĩ Hùng', username='bacsi', password=pw, user_role=UserRole.DOCTOR)
            u4 = User(name='Thu Ngân Mai', username='thungan', password=pw, user_role=UserRole.CASHIER)
            db.session.add_all([u1, u2, u3, u4])

        # Tạo quy định mặc định
        if not QuyDinh.query.first():
            db.session.add(QuyDinh(so_benh_nhan_toi_da=40, tien_kham=100000))

        # Tạo 3 đơn vị thuốc & thuốc mẫu
        if not DonViThuoc.query.first():
            dv1 = DonViThuoc(ten_don_vi='viên')
            dv2 = DonViThuoc(ten_don_vi='chai')
            dv3 = DonViThuoc(ten_don_vi='vĩ')
            db.session.add_all([dv1, dv2, dv3])
            db.session.flush()

            db.session.add_all([
                Thuoc(ten_thuoc='Paracetamol 500mg', don_gia=2000, don_vi_id=dv1.id),
                Thuoc(ten_thuoc='Amoxicillin 500mg', don_gia=15000, don_vi_id=dv3.id),
                Thuoc(ten_thuoc='Siro ho Prospan', don_gia=75000, don_vi_id=dv2.id),
                Thuoc(ten_thuoc='Vitamin C 500mg', don_gia=1500, don_vi_id=dv1.id)
            ])

        db.session.commit()
        print("Khởi tạo CSDL và dữ liệu mẫu thành công!")