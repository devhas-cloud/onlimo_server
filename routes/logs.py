from flask import Blueprint, render_template, request
from flask_login import login_required
from models.data_measurement import DataMeasurement
from models.config_device import ConfigDevice
from datetime import datetime

logs_bp = Blueprint('logs', __name__)

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


@logs_bp.route('/logs')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 50

    device_id = request.args.get('device_id', '')
    status = request.args.get('status', '')
    log_type = request.args.get('log_type', 'dlh')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    devices = ConfigDevice.query.order_by(ConfigDevice.device_id).all()
    device_choices = [(d.device_id, f"{d.device_id} - {d.device_name}") for d in devices]

    query = DataMeasurement.query

    if device_id:
        query = query.filter(DataMeasurement.device_id == device_id)

    if log_type == 'dlh':
        if status:
            query = query.filter(DataMeasurement.dlh_send_status == status)
    else:
        if status:
            query = query.filter(DataMeasurement.has_send_status == status)

    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(DataMeasurement.timestamp >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d')
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
            query = query.filter(DataMeasurement.timestamp <= dt_to)
        except ValueError:
            pass

    query = query.order_by(DataMeasurement.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('logs.html',
        pagination=pagination,
        logs=pagination.items,
        device_choices=device_choices,
        param_columns=PARAM_COLUMNS,
        filters={
            'device_id': device_id,
            'status': status,
            'log_type': log_type,
            'date_from': date_from,
            'date_to': date_to,
        }
    )