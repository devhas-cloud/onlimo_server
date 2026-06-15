import os
import glob
import math
import logging
from models import db
from models.config_device import ConfigDevice
from models.data_measurement import DataMeasurement
from services.csv_parser import parse_csv_file
from services.has_sender import send_to_has

logger = logging.getLogger(__name__)


def run_ftp_watcher(app):
    with app.app_context():
        devices = ConfigDevice.query.filter_by(read_csv_status='active').all()

        for device in devices:
            device_folder = os.path.join(app.config['FTP_ROOT'], device.device_id)

            if not os.path.isdir(device_folder):
                continue

            csv_pattern = os.path.join(device_folder, '*.csv')
            csv_files = sorted(glob.glob(csv_pattern))

            if not csv_files:
                continue

            for csv_file in csv_files:
                logger.info(f"Found {os.path.basename(csv_file)} for device {device.device_id}")

                measurements = parse_csv_file(csv_file, device.device_id)

                if measurements is None:
                    logger.error(f"Error parsing CSV {csv_file} for device {device.device_id}")
                    continue

                if not measurements:
                    logger.warning(f"No valid data in CSV {csv_file} for device {device.device_id}")
                    try:
                        os.remove(csv_file)
                        logger.info(f"Deleted empty CSV {csv_file}")
                    except OSError as e:
                        logger.error(f"Error deleting {csv_file}: {e}")
                    continue

                saved_count = 0
                new_records = []
                for m in measurements:
                    existing = DataMeasurement.query.filter_by(
                        device_id=m['device_id'],
                        timestamp=m['timestamp']
                    ).first()

                    if existing:
                        continue

                    record = DataMeasurement(
                        device_id=m['device_id'],
                        timestamp=m['timestamp'],
                        ph=m.get('ph'),
                        orp=m.get('orp'),
                        tds=m.get('tds'),
                        conduct=m.get('conduct'),
                        do=m.get('do'),
                        salinity=m.get('salinity'),
                        nh3n=m.get('nh3n'),
                        battery=m.get('battery'),
                        depth=m.get('depth'),
                        flow=m.get('flow'),
                        tflow=m.get('tflow'),
                        turb=m.get('turb'),
                        tss=m.get('tss'),
                        cod=m.get('cod'),
                        bod=m.get('bod'),
                        no3=m.get('no3'),
                        wtemp=m.get('wtemp'),
                        wpress=m.get('wpress'),
                        dlh_send_status='pending',
                        has_send_status='pending'
                    )
                    db.session.add(record)
                    new_records.append(record)
                    saved_count += 1

                try:
                    db.session.commit()
                    logger.info(f"Saved {saved_count} new measurements from {os.path.basename(csv_file)} for device {device.device_id}")

                    try:
                        os.remove(csv_file)
                        logger.info(f"Deleted {csv_file} for device {device.device_id}")
                    except OSError as e:
                        logger.error(f"Error deleting {csv_file} for device {device.device_id}: {e}")

                    if new_records:
                        try:
                            send_to_has(device.device_id, new_records)
                        except Exception as e:
                            logger.error(f"Error sending to HAS for device {device.device_id}: {e}")

                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error saving measurements from {csv_file} for device {device.device_id}: {e}")