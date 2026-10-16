"""
SQLAlchemy models for the Smart Campus Electronics Rental & Asset Management
System. The schema here is the single source of truth and matches exactly what
seed_data.py, verify_and_seed.py, migrate_db.py and the test suite expect.
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def _utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student | staff | admin
    student_id = db.Column(db.String(60))
    department = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    trust_score = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=_utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True, foreign_keys='Booking.user_id')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    fines = db.relationship('Fine', backref='user', lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def first_name(self):
        return (self.name or '').split(' ')[0]

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class DeviceCategory(db.Model):
    __tablename__ = 'device_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    icon = db.Column(db.String(60), default='box')
    description = db.Column(db.Text)

    devices = db.relationship('Device', backref='category', lazy=True)

    def __repr__(self):
        return f"<DeviceCategory {self.name}>"


class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    device_code = db.Column(db.String(60), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('device_categories.id'), nullable=False)
    brand = db.Column(db.String(120))
    model = db.Column(db.String(120))
    serial_number = db.Column(db.String(120))
    price_per_day = db.Column(db.Float, nullable=False, default=0.0)
    deposit_amount = db.Column(db.Float, nullable=False, default=0.0)
    is_non_electronic = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(30), default='available')  # available | rented | maintenance
    condition = db.Column(db.String(40), default='Good')
    location = db.Column(db.String(160))
    tags = db.Column(db.Text)
    specs = db.Column(db.JSON)
    image_url = db.Column(db.String(400))
    qr_code_path = db.Column(db.String(400))

    bookings = db.relationship('Booking', backref='device', lazy=True)

    @property
    def specs_dict(self):
        return self.specs or {}

    def __repr__(self):
        return f"<Device {self.device_code} {self.name}>"


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(60), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, default=1)
    total_amount = db.Column(db.Float, default=0.0)
    purpose = db.Column(db.Text)
    # pending_approval | approved | active | completed | rejected | cancelled
    status = db.Column(db.String(30), default='pending_approval')
    created_at = db.Column(db.DateTime, default=_utcnow)

    payments = db.relationship('Payment', backref='booking', lazy=True)
    rental = db.relationship('Rental', backref='booking', uselist=False, lazy=True)

    def __repr__(self):
        return f"<Booking {self.booking_code} {self.status}>"


class Rental(db.Model):
    __tablename__ = 'rentals'

    id = db.Column(db.Integer, primary_key=True)
    rental_code = db.Column(db.String(60), unique=True, nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    issued_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    issued_at = db.Column(db.DateTime, default=_utcnow)
    due_date = db.Column(db.Date)
    returned_at = db.Column(db.DateTime)
    received_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    initial_condition_notes = db.Column(db.Text)
    initial_image_path = db.Column(db.String(400))
    status = db.Column(db.String(30), default='active')  # active | overdue | returned

    device = db.relationship('Device', foreign_keys=[device_id])
    renter = db.relationship('User', foreign_keys=[user_id])
    inspection = db.relationship('ReturnInspection', backref='rental', uselist=False, lazy=True)

    def __repr__(self):
        return f"<Rental {self.rental_code} {self.status}>"


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_code = db.Column(db.String(60), unique=True, nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    payment_type = db.Column(db.String(30), default='rental')  # rental | deposit | fine
    payment_method = db.Column(db.String(60))
    transaction_id = db.Column(db.String(120))
    status = db.Column(db.String(30), default='pending')  # pending | paid | refunded
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f"<Payment {self.payment_code} {self.status}>"


class Fine(db.Model):
    __tablename__ = 'fines'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'))
    reason = db.Column(db.Text)
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='pending')  # pending | paid | waived
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f"<Fine {self.amount} {self.status}>"


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    type = db.Column(db.String(30), default='info')  # info | success | warning | danger
    action_link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f"<Notification {self.title}>"


class ReturnInspection(db.Model):
    __tablename__ = 'return_inspections'

    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)
    inspected_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ai_damage_detected = db.Column(db.Boolean, default=False)
    damage_score = db.Column(db.Float, default=0.0)
    ai_analysis_summary = db.Column(db.Text)
    damage_description = db.Column(db.Text)
    diff_image_path = db.Column(db.String(400))
    staff_notes = db.Column(db.Text)
    fine_imposed = db.Column(db.Float, default=0.0)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f"<ReturnInspection rental={self.rental_id} score={self.damage_score}>"


class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    cost = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='open')  # open | in_progress | resolved
    created_at = db.Column(db.DateTime, default=_utcnow)

    device = db.relationship('Device')

    def __repr__(self):
        return f"<MaintenanceLog device={self.device_id} {self.status}>"
