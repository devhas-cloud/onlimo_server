from models import db


class DataMeasurement(db.Model):
    __tablename__ = 'data_measurements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(255), db.ForeignKey('config_device.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    ph = db.Column(db.Float, nullable=True)
    orp = db.Column(db.Float, nullable=True)
    tds = db.Column(db.Float, nullable=True)
    conduct = db.Column(db.Float, nullable=True)
    do = db.Column(db.Float, nullable=True)
    salinity = db.Column(db.Float, nullable=True)
    nh3n = db.Column(db.Float, nullable=True)
    battery = db.Column(db.Float, nullable=True)
    depth = db.Column(db.Float, nullable=True)
    flow = db.Column(db.Float, nullable=True)
    tflow = db.Column(db.Float, nullable=True)
    turb = db.Column(db.Float, nullable=True)
    tss = db.Column(db.Float, nullable=True)
    cod = db.Column(db.Float, nullable=True)
    bod = db.Column(db.Float, nullable=True)
    no3 = db.Column(db.Float, nullable=True)
    wtemp = db.Column(db.Float, nullable=True)
    wpress = db.Column(db.Float, nullable=True)
    dlh_send_status = db.Column(db.String(50), nullable=False, default='pending')
    dlh_response = db.Column(db.Text, nullable=True)
    has_send_status = db.Column(db.String(50), nullable=False, default='pending')
    has_response = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<DataMeasurement {self.device_id} {self.timestamp}>'