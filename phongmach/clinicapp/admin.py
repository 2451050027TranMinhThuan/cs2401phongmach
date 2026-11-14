from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, request
from clinicapp.models import Thuoc, DonViThuoc, QuyDinh, UserRole
from clinicapp import app, db, dao
from datetime import date


class AuthenticatedAdmin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class ThuocView(AuthenticatedAdmin):
    column_list = ['id', 'ten_thuoc', 'don_gia', 'don_vi']
    column_searchable_list = ['ten_thuoc']
    column_filters = ['don_gia', 'don_vi_id']
    can_export = True


class QuyDinhView(AuthenticatedAdmin):
    can_create = False
    can_delete = False
    column_labels = {
        'so_benh_nhan_toi_da': 'Số bệnh nhân tối đa/ngày',
        'tien_kham': 'Tiền khám mặc định (VNĐ)'
    }


class StatsView(AuthenticatedView):
    @expose('/')
    def index(self):
        month = int(request.args.get('month', date.today().month))
        year = int(request.args.get('year', date.today().year))
        rev_stats = dao.stats_revenue_by_month(month, year)
        total_rev = sum(r[2] for r in rev_stats) if rev_stats else 0
        med_stats = dao.stats_medicine_by_month(month, year)
        return self.render('admin/stats.html', month=month, year=year,
                           rev_stats=rev_stats, total_rev=total_rev, med_stats=med_stats)


class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


admin = Admin(app=app, name='QUẢN TRỊ PHÒNG MẠCH', template_mode='bootstrap4', index_view=MyAdminIndexView())
admin.add_view(ThuocView(Thuoc, db.session, name='Quản lý Thuốc'))
admin.add_view(AuthenticatedAdmin(DonViThuoc, db.session, name='Đơn vị Thuốc'))
admin.add_view(QuyDinhView(QuyDinh, db.session, name='Thay đổi Quy định'))
admin.add_view(StatsView(name='Thống kê Báo cáo'))
admin.add_view(LogoutView(name='Đăng xuất'))