"""
Public catalog + student-facing routes: landing page, device catalog, AI
assistant, dashboard, bookings, rentals, AI returns, and the Razorpay payment
flow.
"""
import uuid
from datetime import datetime, date, timezone, timedelta

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify,
    current_app
)
from flask_login import login_required, current_user

from app.models import (
    db, Device, DeviceCategory, Booking, Rental, Payment, Fine,
    Notification, ReturnInspection
)
from app.ai.recommender import recommend_devices
from app.ai.damage_detector import analyze_return

student_bp = Blueprint('student', __name__)


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@student_bp.route('/')
def index():
    categories = DeviceCategory.query.all()
    featured = Device.query.filter_by(status='available').limit(6).all()
    stats = {
        'devices': Device.query.count(),
        'categories': DeviceCategory.query.count(),
        'available': Device.query.filter_by(status='available').count(),
    }
    return render_template('index.html', categories=categories,
                           featured=featured, stats=stats)


@student_bp.route('/devices')
def devices():
    category_id = request.args.get('category', type=int)
    search = (request.args.get('q') or '').strip()
    query = Device.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(Device.name.ilike(like),
                                    Device.tags.ilike(like),
                                    Device.brand.ilike(like)))
    devices = query.all()
    categories = DeviceCategory.query.all()
    return render_template('student/devices.html', devices=devices,
                           categories=categories, active_cat=category_id,
                           search=search)


@student_bp.route('/device/<int:device_id>')
def device_detail(device_id):
    device = Device.query.get_or_404(device_id)
    related = Device.query.filter(Device.category_id == device.category_id,
                                  Device.id != device.id).limit(4).all()
    return render_template('student/device_detail.html', device=device,
                           related=related)


@student_bp.route('/ai-assistant')
def ai_assistant():
    query = (request.args.get('query') or '').strip()
    results = []
    if query:
        results = recommend_devices(query, Device.query.all(), top_n=6)
    return render_template('student/ai_assistant.html', query=query,
                           results=results)


# ---------------------------------------------------------------------------
# Student dashboard & lists (auth required)
# ---------------------------------------------------------------------------
@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    if current_user.role == 'staff':
        return redirect(url_for('staff.dashboard'))

    active = Rental.query.filter_by(user_id=current_user.id).filter(
        Rental.status.in_(['active', 'overdue'])).all()
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    pending_fines = Fine.query.filter_by(user_id=current_user.id,
                                         status='pending').all()
    recommendations = recommend_devices('', Device.query.filter_by(
        status='available').all(), top_n=4)
    stats = {
        'active_rentals': len(active),
        'total_bookings': len(bookings),
        'pending_fines': sum(f.amount for f in pending_fines),
        'available_devices': Device.query.filter_by(status='available').count(),
    }
    return render_template('student/dashboard.html', active=active,
                           bookings=bookings, stats=stats,
                           recommendations=recommendations,
                           pending_fines=pending_fines)


@student_bp.route('/active-rentals')
@login_required
def active_rentals():
    rentals = Rental.query.filter_by(user_id=current_user.id).filter(
        Rental.status.in_(['active', 'overdue'])).all()
    return render_template('student/active_rentals.html', rentals=rentals,
                           today=date.today())


@student_bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(
        Booking.created_at.desc()).all()
    return render_template('student/my_bookings.html', bookings=bookings)


@student_bp.route('/notifications')
@login_required
def notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()).all()
    # Mark as read on view
    for n in notes:
        n.is_read = True
    db.session.commit()
    return render_template('student/notifications.html', notifications=notes)


# ---------------------------------------------------------------------------
# Booking flow
# ---------------------------------------------------------------------------
@student_bp.route('/book/<int:device_id>', methods=['GET', 'POST'])
@login_required
def book(device_id):
    device = Device.query.get_or_404(device_id)
    if request.method == 'POST':
        start = _parse_date(request.form.get('start_date'), date.today())
        end = _parse_date(request.form.get('end_date'), date.today() + timedelta(days=1))
        if end < start:
            end = start
        total_days = max(1, (end - start).days)
        purpose = request.form.get('purpose', '')

        booking = Booking(
            booking_code=f"BKG-{uuid.uuid4().hex[:8].upper()}",
            user_id=current_user.id, device_id=device.id,
            start_date=start, end_date=end, total_days=total_days,
            total_amount=device.price_per_day * total_days,
            purpose=purpose, status='pending_approval')
        db.session.add(booking)
        db.session.commit()
        flash('Booking request submitted for approval.', 'success')
        return redirect(url_for('student.payment', booking_id=booking.id))

    return render_template('student/book.html', device=device,
                           today=date.today().isoformat())


# ---------------------------------------------------------------------------
# Razorpay payment flow
# ---------------------------------------------------------------------------
@student_bp.route('/payment/<int:booking_id>')
@login_required
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    device = Device.query.get(booking.device_id)
    deposit = device.deposit_amount if device else 0.0
    payable = (booking.total_amount or 0) + (deposit or 0)

    # Create a Razorpay order when SDK + real keys are available; otherwise
    # fall back to a demo ORDER_ID so the checkout modal still renders.
    order_id = f"order_demo_{uuid.uuid4().hex[:12]}"
    key_id = current_app.config.get('RAZORPAY_KEY_ID', '')
    try:
        import razorpay
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', '')
        client = razorpay.Client(auth=(key_id, key_secret))
        order = client.order.create({
            'amount': int(payable * 100),
            'currency': 'INR',
            'payment_capture': 1,
        })
        order_id = order.get('id', order_id)
    except Exception:
        # Offline / test mode: keep the demo order id.
        pass

    return render_template('student/payment.html', booking=booking,
                           device=device, deposit=deposit, payable=payable,
                           order_id=order_id, razorpay_key_id=key_id)


@student_bp.route('/payment/verify/<int:booking_id>', methods=['POST'])
@login_required
def payment_verify(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json(silent=True) or {}
    payment_id = data.get('razorpay_payment_id', f"pay_{uuid.uuid4().hex[:12]}")
    method = data.get('payment_method', 'Razorpay')

    payment = Payment(
        payment_code=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        booking_id=booking.id, user_id=booking.user_id,
        amount=booking.total_amount, payment_type='rental',
        payment_method=method, transaction_id=payment_id, status='paid')
    db.session.add(payment)

    if booking.status in ('pending_approval', 'approved'):
        booking.status = 'approved'
    db.session.commit()

    return jsonify({
        'success': True,
        'tx_id': payment_id,
        'message': 'Payment verified and recorded successfully.',
        'redirect': url_for('student.my_bookings'),
    })


# ---------------------------------------------------------------------------
# AI return + inspection
# ---------------------------------------------------------------------------
@student_bp.route('/return-device/<int:rental_id>', methods=['GET', 'POST'])
@login_required
def return_device(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    device = Device.query.get(rental.device_id)
    inspection = ReturnInspection.query.filter_by(rental_id=rental.id).first()

    if request.method == 'POST':
        if 'demo_damage' in request.form:
            scenario = 'damage'
        elif 'demo_clean' in request.form:
            scenario = 'clean'
        else:
            scenario = 'clean'

        result = analyze_return(scenario=scenario)

        # Update existing inspection to avoid duplicates on re-test.
        if not inspection:
            inspection = ReturnInspection(rental_id=rental.id)
            db.session.add(inspection)
        inspection.inspected_by_id = current_user.id
        inspection.ai_damage_detected = result['damage_detected']
        inspection.damage_score = result['score']
        inspection.ai_analysis_summary = result['summary']
        inspection.damage_description = result['description']
        inspection.diff_image_path = result['diff_image_path']
        inspection.fine_imposed = result['suggested_fine']
        inspection.verified = True

        rental.status = 'returned'
        rental.returned_at = datetime.now(timezone.utc)
        rental.received_by_id = current_user.id
        if device:
            device.status = 'available'

        # Raise a fine when damage warrants it (one per inspection).
        if result['suggested_fine'] > 0:
            existing_fine = Fine.query.filter_by(
                rental_id=rental.id, status='pending').first()
            if not existing_fine:
                db.session.add(Fine(
                    user_id=rental.user_id, rental_id=rental.id,
                    reason=f"AI-detected damage ({result['score']}% severity)",
                    amount=result['suggested_fine'], status='pending'))

        db.session.commit()
        flash('AI return inspection completed.', 'success')
        return render_template('student/return_device.html', rental=rental,
                               device=device, inspection=inspection,
                               just_returned=True)

    return render_template('student/return_device.html', rental=rental,
                           device=device, inspection=inspection,
                           just_returned=False)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _parse_date(value, default):
    if not value:
        return default
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return default
