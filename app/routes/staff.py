"""
Staff / Lab-technician routes: dashboard, QR scanner, issue gear, receive
returns, and inspection detail.
"""
from datetime import datetime, date, timezone
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort
)
from flask_login import login_required, current_user

from app.models import (
    db, Device, Booking, Rental, ReturnInspection, User
)

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in ('staff', 'admin'):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@staff_bp.route('/dashboard')
@staff_required
def dashboard():
    pending_issue = Booking.query.filter_by(status='approved').all()
    active_rentals = Rental.query.filter(
        Rental.status.in_(['active', 'overdue'])).all()
    awaiting_return = Rental.query.filter_by(status='active').all()
    stats = {
        'to_issue': len(pending_issue),
        'active': len(active_rentals),
        'awaiting_return': len(awaiting_return),
        'devices': Device.query.count(),
    }
    return render_template('staff/dashboard.html', pending_issue=pending_issue,
                           active_rentals=active_rentals, stats=stats,
                           today=date.today())


@staff_bp.route('/scanner')
@staff_required
def scanner():
    return render_template('staff/qr_scanner.html')


@staff_bp.route('/inspection')
@staff_required
def inspection():
    inspections = ReturnInspection.query.order_by(
        ReturnInspection.created_at.desc()).all()
    return render_template('staff/inspection.html', inspections=inspections)


@staff_bp.route('/inspection/<int:inspection_id>')
@staff_required
def inspection_detail(inspection_id):
    insp = ReturnInspection.query.get_or_404(inspection_id)
    rental = Rental.query.get(insp.rental_id)
    device = Device.query.get(rental.device_id) if rental else None
    return render_template('staff/inspection_detail.html', inspection=insp,
                           rental=rental, device=device)


@staff_bp.route('/issue/<int:booking_id>', methods=['POST'])
@staff_required
def issue_device(booking_id):
    import uuid
    booking = Booking.query.get_or_404(booking_id)
    device = Device.query.get(booking.device_id)
    rental = Rental(
        rental_code=f"RNT-{uuid.uuid4().hex[:8].upper()}",
        booking_id=booking.id, user_id=booking.user_id,
        device_id=booking.device_id, issued_by_id=current_user.id,
        issued_at=datetime.now(timezone.utc), due_date=booking.end_date,
        initial_condition_notes=request.form.get('notes', ''),
        status='active')
    booking.status = 'active'
    if device:
        device.status = 'rented'
    db.session.add(rental)
    db.session.commit()
    flash(f'Device issued to {booking.user.name}.', 'success')
    return redirect(url_for('staff.dashboard'))
