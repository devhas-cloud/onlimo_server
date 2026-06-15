import logging
import requests
from datetime import datetime
from models import db
from models.has_config import HasConfig
from models.data_measurement import DataMeasurement

logger = logging.getLogger(__name__)

ALL_PARAM_FIELDS = [
    'ph', 'orp', 'tds', 'conduct', 'do', 'salinity', 'nh3n',
    'battery', 'depth', 'flow', 'tflow', 'turb', 'tss', 'cod',
    'bod', 'no3', 'wtemp', 'wpress'
]


def send_to_has(device_id, records):
    has_config = HasConfig.query.first()

    if not has_config or has_config.has_status != 'active':
        logger.info(f"HAS Portal inactive, skipping send for device {device_id}")
        return False

    if not all([has_config.has_api_url, has_config.has_api_key]):
        logger.warning("HAS Portal config incomplete")
        return False

    if has_config.has_params:
        selected_params = [p.strip() for p in has_config.has_params.split(',') if p.strip()]
    else:
        selected_params = ALL_PARAM_FIELDS

    data_list = []
    for record in records:
        if isinstance(record.timestamp, datetime):
            recorded_at = record.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            timestamp_unix = int(record.timestamp.timestamp())
        else:
            recorded_at = str(record.timestamp)
            timestamp_unix = 0

        for param in selected_params:
            if param not in ALL_PARAM_FIELDS:
                continue
            val = getattr(record, param, None)
            if val is not None:
                data_list.append({
                    'recorded_at': recorded_at,
                    'timestamp': timestamp_unix,
                    'parameter_name': param,
                    'value': val,
                })

    if not data_list:
        logger.info(f"No data to send to HAS for device {device_id}")
        return False

    payload = {
        'device_id': device_id,
        'data': data_list,
    }

    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': has_config.has_api_key,
    }

    url = has_config.has_api_url

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=(5, 10))

        response_text = response.text[:1000] if response.text else 'Empty response'

        if response.status_code in (200, 201):
            for record in records:
                record.has_send_status = 'sent'
                record.has_response = response_text
            logger.info(f"HAS Portal success for device {device_id}, {len(records)} records")
        else:
            for record in records:
                record.has_send_status = 'failed'
                record.has_response = response_text
            logger.warning(f"HAS Portal failed for device {device_id}: {response.status_code}")

    except requests.Timeout:
        for record in records:
            record.has_send_status = 'failed'
            record.has_response = 'Timeout'
        logger.error(f"HAS Portal timeout for device {device_id}")

    except requests.RequestException as e:
        for record in records:
            record.has_send_status = 'failed'
            record.has_response = f'RequestException: {e}'
        logger.error(f"HAS Portal request error for device {device_id}: {e}")

    except Exception as e:
        for record in records:
            record.has_send_status = 'failed'
            record.has_response = f'Error: {e}'
        logger.error(f"HAS Portal unexpected error for device {device_id}: {e}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error committing HAS send status for device {device_id}: {e}")

    return True