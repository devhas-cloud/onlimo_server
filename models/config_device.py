from models import db


class ConfigDevice(db.Model):
    __tablename__ = 'config_device'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.String(255), unique=True, nullable=False)
    device_name = db.Column(db.String(255), nullable=False)
    userftp = db.Column(db.String(255), nullable=False, default='onlimo')
    passwordftp = db.Column(db.String(255), nullable=False, default='onlimo_pass_2026')
    dlh_status = db.Column(db.String(50), nullable=False, default='inactive')
    dlh_api_url = db.Column(db.Text, nullable=True)
    dlh_api_key = db.Column(db.Text, nullable=True)
    dlh_api_secret = db.Column(db.Text, nullable=True)
    dlh_uid = db.Column(db.String(255), nullable=True)
    read_csv_status = db.Column(db.String(50), nullable=False, default='inactive')

    measurements = db.relationship('DataMeasurement', backref='device', lazy=True)

    def __repr__(self):
        return f'<ConfigDevice {self.device_id}>'