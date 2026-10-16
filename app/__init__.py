"""
Flask application factory for the Smart Campus Electronics Rental & Asset
Management System.

Wires up:
  - Configuration (PostgreSQL / Supabase / SQLite via config.py)
  - SQLAlchemy ORM + Flask-Login
  - Upload directories
  - Blueprints: auth, student, staff, admin, api
  - Template globals (notification counts, currency, etc.)
"""
import os
from flask import Flask
from flask_login import LoginManager

from config import Config
from app.models import db, User, Notification

login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # --- Ensure upload directories exist ---
    upload_root = app.config['UPLOAD_FOLDER']
    for sub in ('', 'devices', 'inspections', 'qrcodes'):
        os.makedirs(os.path.join(upload_root, sub), exist_ok=True)

    # --- Ensure the SQLite instance directory exists (local fallback mode) ---
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        sqlite_path = db_uri.replace('sqlite:///', '', 1)
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to continue.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.staff import staff_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # --- Create tables on first run (safe no-op if they already exist) ---
    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:  # pragma: no cover - surfaced at runtime
            app.logger.warning("db.create_all() skipped: %s", exc)

    # --- Template globals ---
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        unread = 0
        if current_user.is_authenticated:
            unread = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return {
            'CURRENCY': app.config.get('DEFAULT_CURRENCY', '₹'),
            'unread_notifications': unread,
            'RAZORPAY_KEY_ID': app.config.get('RAZORPAY_KEY_ID', ''),
        }

    @app.template_filter('inr')
    def inr_filter(value):
        try:
            return f"₹{float(value):,.0f}"
        except (TypeError, ValueError):
            return value

    return app
