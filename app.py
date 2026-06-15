import os
import logging
from flask import Flask
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
from models import db
from models.admin import Admin
from models.has_config import HasConfig
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Silakan login terlebih dahulu.'

scheduler = BackgroundScheduler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('onlimo_dlh.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.jinja_env.globals['getattr'] = getattr

    db.init_app(app)
    login_manager.init_app(app)

    from routes import register_blueprints
    register_blueprints(app)

    with app.app_context():
        db.create_all()

        admin = Admin.query.first()
        if not admin:
            admin = Admin(
                username=app.config['ADMIN_USERNAME']
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            logger.info(f"Default admin created: {admin.username}")

        has_config = HasConfig.query.first()
        if not has_config:
            has_config = HasConfig(has_status='inactive', has_api_url='', has_api_key='')
            db.session.add(has_config)
            db.session.commit()

    from services.ftp_watcher import run_ftp_watcher
    from services.dlh_sender import send_dlh_primary, send_dlh_retry

    scheduler.add_job(
        run_ftp_watcher,
        'interval',
        seconds=30,
        args=[app],
        id='ftp_watcher',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=60,
        coalesce=True
    )

    scheduler.add_job(
        send_dlh_primary,
        'cron',
        minute=0,
        second=10,
        args=[app],
        id='dlh_primary',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=120,
        coalesce=True
    )

    scheduler.add_job(
        send_dlh_retry,
        'interval',
        minutes=10,
        args=[app],
        id='dlh_retry',
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=120,
        coalesce=True
    )

    scheduler.start()
    logger.info("Scheduler started: FTP watcher (30s), DLH primary (every hour :10s), DLH retry (10min)")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=os.getenv('APP_HOST', '0.0.0.0'),
        port=int(os.getenv('APP_PORT', 5000)),
        debug=False
    )