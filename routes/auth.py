"""
Authentication routes - login, logout, registration
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from extensions import db
from models.admin import Admin
from models.doctor import Doctor
from models.patient import Patient
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Universal login for all user types"""
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return redirect(url_for('auth.login'))

        # Try to find user in each table
        user = None

        # Check admin
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            if not admin.is_active:
                flash('Your account has been deactivated.', 'danger')
                return redirect(url_for('auth.login'))
            user = admin

        # Check doctor
        if not user:
            doctor = Doctor.query.filter_by(email=email).first()
            if doctor and doctor.check_password(password):
                if doctor.is_blacklisted:
                    flash('Your account has been suspended.', 'danger')
                    return redirect(url_for('auth.login'))
                user = doctor

        # Check patient
        if not user:
            patient = Patient.query.filter_by(email=email).first()
            if patient and patient.check_password(password):
                if patient.is_blacklisted:
                    flash('Your account has been suspended.', 'danger')
                    return redirect(url_for('auth.login'))
                user = patient

        if user:
            login_user(user, remember=True)
            flash(f'Welcome back, {user.name if hasattr(user, "name") else user.username}!', 'success')

            # Redirect to appropriate dashboard
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif user.role == 'patient':
                return redirect(url_for('patient.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Patient registration (self-registration)"""
    if current_user.is_authenticated:
        return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        contact = request.form.get('contact')
        dob = request.form.get('date_of_birth')

        # Validation
        if not all([name, email, password, confirm_password]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.register'))

        # Check if email already exists
        if Patient.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        if Doctor.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        if Admin.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # Create new patient
        patient = Patient(
            name=name,
            email=email,
            contact=contact,
            date_of_birth=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
        )
        patient.set_password(password)

        db.session.add(patient)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
