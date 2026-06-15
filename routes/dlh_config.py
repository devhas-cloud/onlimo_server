from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db
from models.config_device import ConfigDevice

dlh_config_bp = Blueprint('dlh_config', __name__)


@dlh_config_bp.route('/dlh-config')
@login_required
def index():
    devices = ConfigDevice.query.order_by(ConfigDevice.device_id).all()
    return render_template('dlh_config.html', devices=devices)


@dlh_config_bp.route('/dlh-config/<int:device_id>', methods=['GET', 'POST'])
@login_required
def edit(device_id):
    device = ConfigDevice.query.get_or_404(device_id)

    if request.method == 'POST':
        device.dlh_status = request.form.get('dlh_status', 'inactive')
        device.dlh_api_url = request.form.get('dlh_api_url', '').strip() or None
        device.dlh_api_key = request.form.get('dlh_api_key', '').strip() or None
        device.dlh_api_secret = request.form.get('dlh_api_secret', '').strip() or None
        device.dlh_uid = request.form.get('dlh_uid', '').strip() or None

        db.session.commit()
        flash(f'Konfigurasi DLH untuk device "{device.device_id}" berhasil diperbarui', 'success')
        return redirect(url_for('dlh_config.index'))

    return render_template('dlh_config.html', device=device, edit_mode=True)