import logging
import requests
from datetime import datetime
from models import db
from models.config_device import ConfigDevice
from models.data_measurement import DataMeasurement
from services.csv_parser import DLH_PARAM_TO_JSON

logger = logging.getLogger(__name__)


def _send_single_record(config, record):
    tanggal = record.timestamp.strftime('%Y-%m-%d')
    jam = record.timestamp.strftime('%H:%M:%S')

    data_json = {
        'data': {
            'IDStasiun': config.dlh_uid,
            'Tanggal': tanggal,
            'Jam': jam,
        },
        'apikey': config.dlh_api_key,
        'apisecret': config.dlh_api_secret,
    }

    for param_key, json_key in DLH_PARAM_TO_JSON.items():
        val = getattr(record, param_key, None)
        data_json['data'][json_key] = val if isinstance(val, (int, float)) else 0.0

    url = config.dlh_api_url
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, json=data_json, headers=headers, timeout=(5, 10))

        if not response.text:
            logger.warning(f"DLH API empty response for device {config.device_id} at {tanggal} {jam}")
            return 'failed', 'Empty response'

        try:
            json_response = response.json()
        except ValueError:
            logger.warning(f"DLH API invalid JSON for device {config.device_id}")
            return 'failed', f'Invalid JSON: {response.text[:500]}'

        status_code = json_response.get('status', {}).get('statusCode')
        status_desc = json_response.get('status', {}).get('statusDesc', 'No description')

        if response.status_code == 200 and status_code == 200:
            logger.info(f"DLH success for device {config.device_id} at {tanggal} {jam}")
            return 'sent', response.text[:1000]
        else:
            logger.warning(f"DLH failed for device {config.device_id}: {status_code} {status_desc}")
            return 'failed', response.text[:1000]

    except requests.Timeout:
        logger.error(f"DLH API timeout for device {config.device_id}")
        return 'failed', 'Timeout'

    except requests.RequestException as e:
        logger.error(f"DLH API request error for device {config.device_id}: {e}")
        return 'failed', f'RequestException: {e}'

    except Exception as e:
        logger.error(f"DLH API unexpected error for device {config.device_id}: {e}")
        return 'failed', f'Error: {e}'


def send_dlh_primary(app):
    with app.app_context():
        active_devices = ConfigDevice.query.filter_by(dlh_status='active').all()

        for device in active_devices:
            if not all([device.dlh_api_url, device.dlh_api_key, device.dlh_api_secret, device.dlh_uid]):
                logger.warning(f"DLH config incomplete for device {device.device_id}")
                continue

            pending = DataMeasurement.query.filter(
                DataMeasurement.device_id == device.device_id,
                DataMeasurement.dlh_send_status == 'pending',
                DataMeasurement.timestamp <= datetime.now()
            ).order_by(DataMeasurement.timestamp.asc()).all()

            if not pending:
                continue

            for record in pending:
                status, response_text = _send_single_record(device, record)
                record.dlh_send_status = status
                record.dlh_response = response_text

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error committing DLH send status for device {device.device_id}: {e}")


def send_dlh_retry(app):
    with app.app_context():
        active_devices = ConfigDevice.query.filter_by(dlh_status='active').all()

        for device in active_devices:
            if not all([device.dlh_api_url, device.dlh_api_key, device.dlh_api_secret, device.dlh_uid]):
                continue

            retry_data = DataMeasurement.query.filter(
                DataMeasurement.device_id == device.device_id,
                DataMeasurement.dlh_send_status.in_(['pending', 'failed']),
            ).order_by(DataMeasurement.timestamp.asc()).all()

            if not retry_data:
                continue

            for record in retry_data:
                status, response_text = _send_single_record(device, record)
                record.dlh_send_status = status
                record.dlh_response = response_text

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error committing DLH retry status for device {device.device_id}: {e}")