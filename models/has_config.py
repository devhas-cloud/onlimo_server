from models import db


class HasConfig(db.Model):
    __tablename__ = 'has_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    has_status = db.Column(db.String(50), nullable=False, default='inactive')
    has_api_url = db.Column(db.Text, nullable=True)
    has_api_key = db.Column(db.String(255), nullable=True)
    has_params = db.Column(db.Text, nullable=True, default='ph,tds,do,wtemp,turb,depth,no3,nh3n,cod,bod,tss')

    def __repr__(self):
        return f'<HasConfig status={self.has_status}>'