from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.devices import devices_bp
from routes.data import data_bp
from routes.dlh_config import dlh_config_bp
from routes.has_config import has_config_bp
from routes.logs import logs_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(dlh_config_bp)
    app.register_blueprint(has_config_bp)
    app.register_blueprint(logs_bp)