from flask import Blueprint, render_template, request
from flask_login import login_required
from models.data_measurement import DataMeasurement
from models.config_device import ConfigDevice
from datetime import datetime

data_bp = Blueprint('data', __name__)

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


@data_bp.route('/data')
@login_required
def index():
    devices = ConfigDevice.query.order_by(ConfigDevice.device_id).all()
    device_choices = [(d.device_id, f"{d.device_id} - {d.device_name}") for d in devices]

    page = request.args.get('page', 1, type=int)
    per_page = 20

    device_id = request.args.get('device_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    dlh_status = request.args.get('dlh_status', '')
    has_status = request.args.get('has_status', '')

    query = DataMeasurement.query

    if device_id:
        query = query.filter(DataMeasurement.device_id == device_id)
    if dlh_status:
        query = query.filter(DataMeasurement.dlh_send_status == dlh_status)
    if has_status:
        query = query.filter(DataMeasurement.has_send_status == has_status)
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

    return render_template('data.html',
        device_choices=device_choices,
        param_columns=PARAM_COLUMNS,
        data=pagination.items,
        pagination=pagination,
        filters={
            'device_id': device_id,
            'date_from': date_from,
            'date_to': date_to,
            'dlh_status': dlh_status,
            'has_status': has_status,
        }
    )