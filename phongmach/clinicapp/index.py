from flask import render_template, request, redirect, url_for, flash
from clinicapp import app, db, login, dao, admin
from clinicapp.models import BenhNhan, DanhSachKham, PhieuKham, ChiTietToaThuoc, HoaDon, UserRole
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, date
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE user MODIFY user_role ENUM('ADMIN','NURSE','DOCTOR','CASHIER','PATIENT')"))
        db.session.commit()
    except Exception:
        db.session.rollback()

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.context_processor
def common_responses():
    return {
        'UserRole': UserRole,
        'quy_dinh': dao.get_quy_dinh()
    }


@app.route('/login', methods=['GET', 'POST'])
def login_process():
    err_msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username=username, password=password)
        if user:
            login_user(user=user)
            if user.user_role == UserRole.ADMIN:
                return redirect('/admin')
            elif user.user_role == UserRole.DOCTOR:
                return redirect(url_for('doctor_page'))
            elif user.user_role == UserRole.CASHIER:
                return redirect(url_for('cashier_page'))
            elif user.user_role == UserRole.PATIENT:
                return redirect(url_for('index'))
            return redirect(url_for('nurse_page'))
        else:
            err_msg = 'Tên đăng nhập hoặc mật khẩu không chính xác!'
    return render_template('login.html', err_msg=err_msg)


@app.route('/logout')
def logout_process():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register_process():
    err_msg = ''
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not password or not confirm or password != confirm:
            err_msg = 'Mật khẩu xác nhận không khớp!'
        else:
            try:
                dao.create_user(name=name, username=username, password=password)
                flash('Đăng ký tài khoản thành công! Vui lòng đăng nhập.', 'success')
                return redirect(url_for('login_process'))
            except Exception as ex:
                db.session.rollback()
                err_msg = f'Lỗi đăng ký: {str(ex)}'

    return render_template('register.html', err_msg=err_msg)

@app.route('/', methods=['GET', 'POST'])
def index():
    ngay_str = str(date.today())
    qd = dao.get_quy_dinh()

    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('login_process'))
        ngay_dat_str = request.form.get('ngay_kham', ngay_str)
        ngay_dat = datetime.strptime(ngay_dat_str, '%Y-%m-%d').date()
        ds_kham = dao.load_danh_sach_kham(ngay_dat)

        if len(ds_kham) >= qd.so_benh_nhan_toi_da:
            flash(f'Rất tiếc! Ngày {ngay_dat} đã đủ {qd.so_benh_nhan_toi_da} bệnh nhân. Vui lòng chọn ngày khác!', 'danger')
        else:
            bn = dao.get_or_create_benh_nhan(
                ho_ten=request.form.get('ho_ten'),
                gioi_tinh=request.form.get('gioi_tinh'),
                nam_sinh=request.form.get('nam_sinh'),
                dia_chi=request.form.get('dia_chi'),
                so_dien_thoai=request.form.get('so_dien_thoai')
            )

            dsk = DanhSachKham(ngay_kham=ngay_dat, benh_nhan_id=bn.id)
            db.session.add(dsk)
            db.session.commit()

            dao.send_sms_twilio(bn.so_dien_thoai, f"Phong mach DATATU: Ban da dat lich kham ngay {ngay_dat} thanh cong.")
            flash(f'Đặt lịch khám ngày {ngay_dat} thành công! Tin nhắn SMS xác nhận đã được gửi.', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', ngay_kham=ngay_str)

@app.route('/nurse', methods=['GET', 'POST'])
@login_required
def nurse_page():
    ngay_str = request.args.get('ngay_kham', str(date.today()))
    ngay_kham = datetime.strptime(ngay_str, '%Y-%m-%d').date()
    qd = dao.get_quy_dinh()
    ds_kham = dao.load_danh_sach_kham(ngay_kham)

    if request.method == 'POST':
        if len(ds_kham) >= qd.so_benh_nhan_toi_da:
            flash(f'Quy định: Mỗi ngày chỉ khám tối đa {qd.so_benh_nhan_toi_da} bệnh nhân!', 'danger')
        else:
            bn = dao.get_or_create_benh_nhan(
                ho_ten=request.form.get('ho_ten'),
                gioi_tinh=request.form.get('gioi_tinh'),
                nam_sinh=request.form.get('nam_sinh'),
                dia_chi=request.form.get('dia_chi'),
                so_dien_thoai=request.form.get('so_dien_thoai')
            )

            dsk = DanhSachKham(ngay_kham=ngay_kham, benh_nhan_id=bn.id)
            db.session.add(dsk)
            db.session.commit()

            dao.send_sms_twilio(bn.so_dien_thoai, f"Phong mach DATATU: Ban da dang ky kham ngay {ngay_kham} thanh cong.")
            flash('Đã thêm bệnh nhân vào danh sách khám & gửi SMS!', 'success')
        return redirect(url_for('nurse_page', ngay_kham=ngay_str))

    return render_template('nurse.html', ds_kham=ds_kham, ngay_kham=ngay_str)

@app.route('/doctor', methods=['GET', 'POST'])
@login_required
def doctor_page():
    ds_cho = dao.load_danh_sach_kham(date.today(), trang_thai='Chờ khám')
    kw = request.args.get('kw')
    thuocs = dao.load_thuocs(kw=kw)
    bn_id = request.args.get('bn_id')
    dsk_id = request.args.get('dsk_id')

    bn_chon = BenhNhan.query.get(bn_id) if bn_id else None
    lich_su = PhieuKham.query.filter_by(benh_nhan_id=bn_id).all() if bn_id else []

    if request.method == 'POST':
        pk = PhieuKham(
            ngay_kham=date.today(),
            trieu_chung=request.form.get('trieu_chung'),
            du_doan_benh=request.form.get('du_doan_benh'),
            benh_nhan_id=int(request.form.get('benh_nhan_id')),
            bac_si_id=current_user.id
        )
        db.session.add(pk)
        db.session.flush()

        for t_id, sl, cd in zip(request.form.getlist('thuoc_id[]'),
                                request.form.getlist('so_luong[]'),
                                request.form.getlist('cach_dung[]')):
            if t_id and int(sl) > 0:
                db.session.add(ChiTietToaThuoc(phieu_kham_id=pk.id, thuoc_id=int(t_id),
                                               so_luong=int(sl), cach_dung=cd))

        dsk = DanhSachKham.query.get(int(request.form.get('dsk_id')))
        dsk.trang_thai = 'Đã khám'
        db.session.commit()
        flash('Lưu phiếu khám bệnh thành công!', 'success')
        return redirect(url_for('doctor_page'))

    return render_template('doctor.html', ds_cho=ds_cho, thuocs=thuocs,
                           bn_chon=bn_chon, lich_su=lich_su, dsk_id=dsk_id)

@app.route('/cashier', methods=['GET', 'POST'])
@login_required
def cashier_page():
    qd = dao.get_quy_dinh()
    phieu_chua_tt = PhieuKham.query.filter(~PhieuKham.hoa_don.has()).all()

    if request.method == 'POST':
        pk = PhieuKham.query.get(int(request.form.get('pk_id')))
        tien_thuoc = sum(ct.so_luong * ct.thuoc.don_gia for ct in pk.chi_tiet_toas)
        tong_tien = qd.tien_kham + tien_thuoc

        hd = HoaDon(phieu_kham_id=pk.id, tien_kham=qd.tien_kham,
                    tien_thuoc=tien_thuoc, tong_tien=tong_tien)
        db.session.add(hd)
        db.session.commit()
        flash(f'Thanh toán hoàn tất! Tổng tiền: {tong_tien:,.0f} VNĐ', 'success')
        return redirect(url_for('cashier_page'))

    return render_template('cashier.html', phieu_chua_tt=phieu_chua_tt)
@app.route('/records')
@login_required
def medical_records_page():
    kw = request.args.get('kw')
    bn_id = request.args.get('bn_id')

    ds_benh_nhan = dao.load_ho_so_benh_an(kw=kw)
    bn_chon = BenhNhan.query.get(bn_id) if bn_id else None
    lich_su_kham = PhieuKham.query.filter_by(benh_nhan_id=bn_id)\
                                  .order_by(PhieuKham.ngay_kham.desc(), PhieuKham.id.desc()).all() if bn_id else []

    return render_template('records.html',
                           ds_benh_nhan=ds_benh_nhan,
                           bn_chon=bn_chon,
                           lich_su_kham=lich_su_kham,
                           kw=kw or '')


if __name__ == '__main__':
    app.run(debug=True)