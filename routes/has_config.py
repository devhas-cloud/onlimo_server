from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db
from models.has_config import HasConfig

has_config_bp = Blueprint('has_config', __name__)

ALL_PARAMS = [
    ('ph', 'pH'),
    ('orp', 'ORP'),
    ('tds', 'TDS'),
    ('conduct', 'Conductivity'),
    ('do', 'DO'),
    ('salinity', 'Salinity'),
    ('nh3n', 'NH3-N'),
    ('battery', 'Battery'),
    ('depth', 'Depth'),
    ('flow', 'Flow'),
    ('tflow', 'Total Flow'),
    ('turb', 'Turbidity'),
    ('tss', 'TSS'),
    ('cod', 'COD'),
    ('bod', 'BOD'),
    ('no3', 'NO3'),
    ('wtemp', 'Water Temp'),
    ('wpress', 'Water Press'),
]


@has_config_bp.route('/has-config', methods=['GET', 'POST'])
@login_required
def index():
    config = HasConfig.query.first()

    if not config:
        config = HasConfig(has_status='inactive', has_api_url='', has_api_key='')
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        config.has_status = request.form.get('has_status', 'inactive')
        config.has_api_url = request.form.get('has_api_url', '').strip() or None
        config.has_api_key = request.form.get('has_api_key', '').strip() or None

        selected_params = request.form.getlist('has_params')
        if selected_params:
            config.has_params = ','.join(selected_params)
        else:
            config.has_params = None

        db.session.commit()
        flash('Konfigurasi HAS Portal berhasil diperbarui', 'success')
        return redirect(url_for('has_config.index'))

    current_params = []
    if config.has_params:
        current_params = [p.strip() for p in config.has_params.split(',') if p.strip()]

    return render_template('has_config.html', config=config, all_params=ALL_PARAMS, current_params=current_params)