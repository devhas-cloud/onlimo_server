from flask import Blueprint, render_template, request
from flask_login import login_required
from models.config_device import ConfigDevice
from models.data_measurement import DataMeasurement
from models.has_config import HasConfig
from sqlalchemy import func
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

PARAM_COLUMNS = [
    ('ph', 'pH'),
    ('orp', 'ORP'),
    ('tds', 'TDS'),
    ('conduct', 'Conduct'),
    ('do', 'DO'),
    ('salinity', 'Salinity'),
    ('nh3n', 'NH3-N'),
    ('battery', 'Battery'),
    ('depth', 'Depth'),
    ('flow', 'Flow'),
    ('tflow', 'TFlow'),
    ('turb', 'Turb'),
    ('tss', 'TSS'),
    ('cod', 'COD'),
    ('bod', 'BOD'),
    ('no3', 'NO3'),
    ('wtemp', 'WTemp'),
    ('wpress', 'WPress'),
]


@dashboard_bp.route('/')
@login_required
def index():
    device_count = ConfigDevice.query.count()
    active_devices = ConfigDevice.query.filter_by(read_csv_status='active').count()
    dlh_active_devices = ConfigDevice.query.filter_by(dlh_status='active').count()

    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_data_count = DataMeasurement.query.filter(
        DataMeasurement.timestamp >= today_start,
        DataMeasurement.timestamp <= today_end
    ).count()

    total_data_count = DataMeasurement.query.count()

    pending_dlh = DataMeasurement.query.filter_by(dlh_send_status='pending').count()
    sent_dlh = DataMeasurement.query.filter_by(dlh_send_status='sent').count()
    failed_dlh = DataMeasurement.query.filter_by(dlh_send_status='failed').count()

    pending_has = DataMeasurement.query.filter_by(has_send_status='pending').count()
    sent_has = DataMeasurement.query.filter_by(has_send_status='sent').count()
    failed_has = DataMeasurement.query.filter_by(has_send_status='failed').count()

    has_config = HasConfig.query.first()

    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = DataMeasurement.query.order_by(
        DataMeasurement.timestamp.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    data = pagination.items

    return render_template('dashboard.html',
        device_count=device_count,
        active_devices=active_devices,
        dlh_active_devices=dlh_active_devices,
        today_data_count=today_data_count,
        total_data_count=total_data_count,
        pending_dlh=pending_dlh,
        sent_dlh=sent_dlh,
        failed_dlh=failed_dlh,
        pending_has=pending_has,
        sent_has=sent_has,
        failed_has=failed_has,
        has_config=has_config,
        param_columns=PARAM_COLUMNS,
        data=data,
        pagination=pagination,
    )