"""
Authentication & registration routes.

Handles the role-aware login / registration portals, the demo quick-login
shortcuts, and all server-side registration validation rules.
"""
import re
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash
)
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db, User

auth_bp = Blueprint('auth', __name__)

# Access keys required to self-register privileged accounts.
STAFF_ACCESS_KEY = 'STAFF-DESK-2026'
ADMIN_ACCESS_KEY = 'ADMIN-MASTER-2026'

ROLE_LABELS = {
    'student': 'Student Rental Portal',
    'staff': 'Staff & Lab Tech Portal',
    'admin': 'Administrator & Lab Director Portal',
}

DEMO_ACCOUNTS = {
    'student': 'student@campus.edu',
    'staff': 'staff@campus.edu',
    'admin': 'admin@campus.edu',
}

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _dashboard_for(role):
    if role == 'admin':
        return url_for('admin.dashboard')
    if role == 'staff':
        return url_for('staff.dashboard')
    return url_for('student.dashboard')


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    role = request.values.get('role', 'student')
    if role not in ROLE_LABELS:
        role = 'student'

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        selected_role = request.form.get('role', role)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return render_template('auth/login.html', role=selected_role,
                                   role_labels=ROLE_LABELS,
                                   error='Invalid email or password. Please try again.')

        if user.role != selected_role:
            return render_template(
                'auth/login.html', role=selected_role, role_labels=ROLE_LABELS,
                error=f'Access Denied: this account is not authorised for the '
                      f'{ROLE_LABELS.get(selected_role, selected_role)}.')

        login_user(user)
        flash(f'Welcome back, {user.first_name}!', 'success')
        return redirect(_dashboard_for(user.role))

    return render_template('auth/login.html', role=role, role_labels=ROLE_LABELS)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    role = request.values.get('role', 'student')
    if role not in ROLE_LABELS:
        role = 'student'

    if request.method == 'POST':
        role = request.form.get('role', 'student')
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        phone = (request.form.get('phone') or '').strip()
        student_id = (request.form.get('student_id') or '').strip()
        department = (request.form.get('department') or '').strip()
        password = request.form.get('password') or ''

        error = _validate_registration(role, name, email, phone, password,
                                       request.form)
        if error:
            return render_template('auth/register.html', role=role,
                                   role_labels=ROLE_LABELS, error=error,
                                   form=request.form)

        if User.query.filter_by(email=email).first():
            return render_template('auth/register.html', role=role,
                                   role_labels=ROLE_LABELS, form=request.form,
                                   error='An account with this email already exists.')

        user = User(name=name, email=email, phone=phone, role=role,
                    student_id=student_id, department=department)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Registration successful! Your campus rental account is ready.',
              'success')
        return redirect(_dashboard_for(role))

    return render_template('auth/register.html', role=role,
                           role_labels=ROLE_LABELS, form={})


def _validate_registration(role, name, email, phone, password, form):
    """Return an error string, or None when the submission is valid."""
    # Name: 1-3 words, letters only
    words = [w for w in name.split() if w]
    if len(words) < 1 or len(words) > 3:
        return 'Full Name must contain 1, 2, or 3 words only.'
    # Letters, spaces and a period (for titles like "Dr.") are allowed; digits
    # and other symbols are not.
    if not re.match(r'^[A-Za-z .]+$', name):
        return 'Full Name can only contain letters (no digits or symbols).'

    # Email
    if not EMAIL_RE.match(email):
        return 'Please enter a valid campus email address.'

    # Phone: normalise +91 / spaces, require a 10-digit Indian mobile
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    if len(digits) != 10 or digits[0] not in '6789':
        return 'Contact phone must be a valid 10-digit mobile number.'

    # Password strength
    if not re.search(r'[A-Z]', password):
        return 'Password must contain at least one uppercase letter.'
    if not re.search(r'[^A-Za-z0-9]', password):
        return 'Password must contain at least one special character.'
    if len(password) < 6:
        return 'Password must be at least 6 characters long.'

    # Privileged role access keys
    if role == 'staff':
        if form.get('staff_access_key') != STAFF_ACCESS_KEY:
            return 'Invalid Staff Authorization Key. Contact the Tech Desk.'
    elif role == 'admin':
        if form.get('admin_access_key') != ADMIN_ACCESS_KEY:
            return 'Invalid Master Administrator Security Key.'

    return None


# ---------------------------------------------------------------------------
# Logout & demo quick-login
# ---------------------------------------------------------------------------
@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('student.index'))


@auth_bp.route('/quick-login/<role>')
def quick_login(role):
    """One-click demo login for the seeded accounts."""
    email = DEMO_ACCOUNTS.get(role)
    if not email:
        flash('Unknown demo role.', 'danger')
        return redirect(url_for('auth.login'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Demo account not seeded yet. Run seed_data.py first.', 'warning')
        return redirect(url_for('auth.login', role=role))
    login_user(user)
    return redirect(_dashboard_for(user.role))
