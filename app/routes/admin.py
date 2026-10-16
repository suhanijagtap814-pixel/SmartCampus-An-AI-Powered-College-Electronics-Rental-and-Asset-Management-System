"""
Admin / Lab-director routes: dashboard, booking approvals, device management,
AI demand predictions, student risk radar, and analytics.
"""
from datetime import date
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user

from app.models import (
    db, Device, DeviceCategory, Booking, Rental, Fine, User, Notification
)
from app.ai.demand_predictor import predict_demand
from app.ai.risk_detector import assess_all_students

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'devices': Device.query.count(),
        'rented': Device.query.filter_by(status='rented').count(),
        'students': User.query.filter_by(role='student').count(),
        'pending_approvals': Booking.query.filter_by(
            status='pending_approval').count(),
        'revenue': db.session.query(db.func.coalesce(
            db.func.sum(Booking.total_amount), 0)).scalar() or 0,
        'pending_fines': db.session.query(db.func.coalesce(
            db.func.sum(Fine.amount), 0)).filter(
            Fine.status == 'pending').scalar() or 0,
    }
    recent_bookings = Booking.query.order_by(
        Booking.created_at.desc()).limit(8).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_bookings=recent_bookings, today=date.today())


@admin_bp.route('/approvals')
@admin_required
def approvals():
    pending = Booking.query.filter_by(status='pending_approval').order_by(
        Booking.created_at.desc()).all()
    recent = Booking.query.filter(Booking.status != 'pending_approval').order_by(
        Booking.created_at.desc()).limit(10).all()
    return render_template('admin/approvals.html', pending=pending,
                           recent=recent)


@admin_bp.route('/approvals/<int:booking_id>/<action>', methods=['POST'])
@admin_required
def decide_booking(booking_id, action):
    booking = Booking.query.get_or_404(booking_id)
    if action == 'approve':
        booking.status = 'approved'
        db.session.add(Notification(
            user_id=booking.user_id, title='Booking Approved',
            message=f'Your booking {booking.booking_code} has been approved.',
            type='success', action_link='/my-bookings'))
        flash('Booking approved.', 'success')
    elif action == 'reject':
        booking.status = 'rejected'
        db.session.add(Notification(
            user_id=booking.user_id, title='Booking Rejected',
            message=f'Your booking {booking.booking_code} was rejected.',
            type='danger', action_link='/my-bookings'))
        flash('Booking rejected.', 'info')
    db.session.commit()
    return redirect(url_for('admin.approvals'))


@admin_bp.route('/devices', methods=['GET', 'POST'])
@admin_required
def manage_devices():
    if request.method == 'POST':
        import uuid
        specs = {}
        name = request.form.get('name', '')
        cat_id = request.form.get('category_id', type=int)
        price = request.form.get('price_per_day', type=float) or 0.0
        device = Device(
            device_code=request.form.get('device_code') or
            f"DEV-{uuid.uuid4().hex[:6].upper()}",
            name=name, category_id=cat_id,
            brand=request.form.get('brand', ''),
            model=request.form.get('model', ''),
            serial_number=request.form.get('serial_number', ''),
            price_per_day=price,
            deposit_amount=request.form.get('deposit_amount', type=float) or
            round(max(300.0, price * 3), 2),
            is_non_electronic=bool(request.form.get('is_non_electronic')),
            status='available',
            condition=request.form.get('condition', 'Good'),
            location=request.form.get('location', ''),
            tags=request.form.get('tags', ''), specs=specs,
            image_url=request.form.get('image_url') or
            '/static/uploads/devices/default.jpg')
        db.session.add(device)
        db.session.commit()
        flash('Device added to catalog.', 'success')
        return redirect(url_for('admin.manage_devices'))

    devices = Device.query.all()
    categories = DeviceCategory.query.all()
    return render_template('admin/add_device.html', devices=devices,
                           categories=categories)


@admin_bp.route('/ai-predictions')
@admin_required
def ai_predictions():
    predictions = predict_demand()
    return render_template('admin/ai_predictions.html', predictions=predictions)


@admin_bp.route('/students')
@admin_required
def students():
    profiles = assess_all_students()
    return render_template('admin/students.html', profiles=profiles)


@admin_bp.route('/analytics')
@admin_required
def analytics():
    categories = DeviceCategory.query.all()
    cat_usage = []
    for c in categories:
        count = Booking.query.join(Device, Booking.device_id == Device.id).filter(
            Device.category_id == c.id).count()
        cat_usage.append({'category': c.name, 'bookings': count,
                          'icon': c.icon})
    cat_usage.sort(key=lambda x: x['bookings'], reverse=True)

    revenue = db.session.query(db.func.coalesce(
        db.func.sum(Booking.total_amount), 0)).scalar() or 0
    total_bookings = Booking.query.count()
    status_breakdown = {}
    for status in ('pending_approval', 'approved', 'active', 'completed',
                   'rejected'):
        status_breakdown[status] = Booking.query.filter_by(status=status).count()

    return render_template('admin/analytics.html', cat_usage=cat_usage,
                           revenue=revenue, total_bookings=total_bookings,
                           status_breakdown=status_breakdown)
