import os
import shutil
import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from models import db
from models.config_device import ConfigDevice
from services.ftp_manager import add_ftp_user, delete_ftp_user
from config import Config

logger = logging.getLogger(__name__)

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('/devices')
@login_required
def index():
    devices = ConfigDevice.query.order_by(ConfigDevice.id.desc()).all()
    return render_template('devices.html', devices=devices)


@devices_bp.route('/devices/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        device_id = request.form.get('device_id', '').strip()
        device_name = request.form.get('device_name', '').strip()
        userftp = request.form.get('userftp', '').strip() or device_id
        passwordftp = request.form.get('passwordftp', '').strip() or 'onlimo_pass_2026'

        if not device_id:
            flash('Device ID wajib diisi', 'danger')
            return redirect(url_for('devices.add'))

        if not device_name:
            flash('Device Name wajib diisi', 'danger')
            return redirect(url_for('devices.add'))

        existing = ConfigDevice.query.filter_by(device_id=device_id).first()
        if existing:
            flash(f'Device ID "{device_id}" sudah ada', 'danger')
            return redirect(url_for('devices.add'))

        device = ConfigDevice(
            device_id=device_id,
            device_name=device_name,
            userftp=userftp,
            passwordftp=passwordftp,
            dlh_status='inactive',
            read_csv_status='inactive'
        )
        db.session.add(device)

        try:
            ftp_root = Config.FTP_ROOT
            device_folder = os.path.join(ftp_root, device_id)
            os.makedirs(device_folder, exist_ok=True)
            logger.info(f"Created folder {device_folder}")
        except Exception as e:
            logger.warning(f"Could not create folder {device_folder}: {e}")

        success, msg = add_ftp_user(userftp, passwordftp)
        if not success:
            db.session.commit()
            flash(f'Device disimpan tetapi pembuatan FTP user gagal: {msg}', 'warning')
            return redirect(url_for('devices.index'))

        db.session.commit()
        flash(f'Device "{device_id}" berhasil ditambahkan', 'success')
        return redirect(url_for('devices.index'))

    return render_template('device_form.html', device=None)


@devices_bp.route('/devices/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    device = ConfigDevice.query.get_or_404(id)

    if request.method == 'POST':
        device.device_name = request.form.get('device_name', '').strip() or device.device_name
        device.userftp = request.form.get('userftp', '').strip() or device.device_id
        device.passwordftp = request.form.get('passwordftp', '').strip() or device.passwordftp
        device.dlh_status = request.form.get('dlh_status', 'inactive')
        device.dlh_api_url = request.form.get('dlh_api_url', '').strip() or None
        device.dlh_api_key = request.form.get('dlh_api_key', '').strip() or None
        device.dlh_api_secret = request.form.get('dlh_api_secret', '').strip() or None
        device.dlh_uid = request.form.get('dlh_uid', '').strip() or None
        device.read_csv_status = request.form.get('read_csv_status', 'inactive')

        db.session.commit()
        flash(f'Device "{device.device_id}" berhasil diperbarui', 'success')
        return redirect(url_for('devices.index'))

    return render_template('device_form.html', device=device)


@devices_bp.route('/devices/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    device = ConfigDevice.query.get_or_404(id)

    success, msg = delete_ftp_user(device.userftp)

    try:
        ftp_root = Config.FTP_ROOT
        device_folder = os.path.join(ftp_root, device.device_id)
        if os.path.exists(device_folder):
            shutil.rmtree(device_folder)
            logger.info(f"Deleted folder {device_folder}")
    except Exception as e:
        logger.warning(f"Could not delete folder for device {device.device_id}: {e}")

    db.session.delete(device)
    db.session.commit()

    if not success:
        flash(f'Device dihapus tetapi penghapusan FTP user gagal: {msg}', 'warning')
    else:
        flash(f'Device "{device.device_id}" berhasil dihapus', 'success')

    return redirect(url_for('devices.index'))