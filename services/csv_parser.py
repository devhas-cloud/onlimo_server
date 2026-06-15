import csv
import math
import logging
from datetime import datetime
from collections import OrderedDict

logger = logging.getLogger(__name__)

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

PARAM_KEYS = [key for key, label in PARAM_COLUMNS]

CSV_COLUMN_MAPPING = {
    'interval': 'interval',
    'interval_timestamp': 'interval',
    'measurement interval': 'interval',

    'ph': 'ph',
    'ph - measured': 'ph',

    'orp': 'orp',
    'orp - measured': 'orp',

    'tds': 'tds',
    'tds - measured': 'tds',

    'conduct': 'conduct',
    'conduct - measured': 'conduct',
    'conductivity - measured': 'conduct',

    'do': 'do',
    'do - measured': 'do',
    'dissolved oxygen - measured': 'do',

    'salinity': 'salinity',
    'salinity - measured': 'salinity',

    'nh3n': 'nh3n',
    'nh3n - measured': 'nh3n',
    'ammonium - measured': 'nh3n',
    'amonia - measured': 'nh3n',
    'ammonia - measured': 'nh3n',

    'battery': 'battery',
    'battery - measured': 'battery',

    'depth': 'depth',
    'depth - measured': 'depth',
    'kedalaman - measured': 'depth',

    'flow': 'flow',
    'debit - measured': 'flow',
    'flow - measured': 'flow',

    'tflow': 'tflow',
    'total flow': 'tflow',

    'turb': 'turb',
    'turbidity - measured': 'turb',
    'turbidit - measured': 'turb',
    'turbidity': 'turb',

    'tss': 'tss',
    'tss - measured': 'tss',
    'tsseq - measured': 'tss',
    'tsseq': 'tss',

    'cod': 'cod',
    'cod - measured': 'cod',
    'codeq - measured': 'cod',
    'codeq': 'cod',

    'bod': 'bod',
    'bod - measured': 'bod',
    'bodeq - measured': 'bod',
    'bodeq': 'bod',

    'no3': 'no3',
    'no3 - measured': 'no3',
    'no3eq - measured': 'no3',
    'no3eq': 'no3',
    'nitrat - measured': 'no3',
    'nitrat': 'no3',

    'wtemp': 'wtemp',
    'temperature - measured': 'wtemp',
    'temperature': 'wtemp',
    'temperat - measured': 'wtemp',
    'suhu - measured': 'wtemp',
    'suhu': 'wtemp',

    'wpress': 'wpress',
    'wpress - measured': 'wpress',
}

DLH_FIELD_ORDER = [
    'wtemp', 'tds', 'do', 'ph', 'turb', 'depth',
    'no3', 'nh3n', 'cod', 'bod', 'tss'
]

DLH_PARAM_TO_JSON = {
    'wtemp': 'Suhu',
    'tds': 'TDS',
    'do': 'DO',
    'ph': 'PH',
    'turb': 'Turbidity',
    'depth': 'Kedalaman',
    'no3': 'Nitrat',
    'nh3n': 'Amonia',
    'cod': 'COD',
    'bod': 'BOD',
    'tss': 'TSS',
}


def _extract_parameter_key(header_text):
    text = header_text.strip().lower()
    text = text.replace('=', ' ').replace('(', ' ').replace(')', ' ').replace('[', ' ').replace(']', ' ')
    text = text.replace('-', ' ').replace('_', ' ')
    parts = text.split()

    for i in range(len(parts)):
        for j in range(len(parts), i, -1):
            candidate = ' '.join(parts[i:j])
            if candidate in CSV_COLUMN_MAPPING:
                return CSV_COLUMN_MAPPING[candidate]

    return None


def parse_csv_file(file_path, device_id):
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')

            try:
                next(reader)
            except StopIteration:
                logger.warning(f"CSV file empty: {file_path}")
                return results

            row2 = None
            try:
                row2 = next(reader)
            except StopIteration:
                logger.warning(f"CSV file has no header row: {file_path}")
                return results

            param_keys = []
            for col in row2[1:]:
                key = _extract_parameter_key(col)
                param_keys.append(key)

            for row in reader:
                if not row or len(row) < 2:
                    continue

                ts_str = row[0].strip()
                try:
                    timestamp = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        timestamp = datetime.strptime(ts_str, '%Y-%m-%d %H:%M')
                    except ValueError:
                        logger.warning(f"Cannot parse timestamp: {ts_str}")
                        continue

                record = {'device_id': device_id, 'timestamp': timestamp}
                for key in PARAM_KEYS:
                    record[key] = None

                for i, val_str in enumerate(row[1:]):
                    if i >= len(param_keys) or param_keys[i] is None:
                        continue

                    param_key = param_keys[i]
                    if param_key not in PARAM_KEYS:
                        continue

                    val_str = val_str.strip()
                    if not val_str:
                        continue

                    try:
                        value = float(val_str)
                    except ValueError:
                        continue

                    if math.isnan(value) or math.isinf(value):
                        value = 0.0

                    record[param_key] = value

                results.append(record)

    except Exception as e:
        logger.error(f"Error parsing CSV {file_path}: {e}")
        return None

    return results