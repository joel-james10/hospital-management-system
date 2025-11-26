"""
Admin routes - dashboard, doctor management, appointments, search
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db, mail
from models.doctor import Doctor
from models.patient import Patient
from models.appointment import Appointment
from models.department import Department
from utils.decorators import admin_required
from flask_mail import Message
import secrets
import string

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='Booked').count()

    stats = {
        'doctors': total_doctors,
        'patients': total_patients,
        'appointments': total_appointments,
        'pending': pending_appointments
    }

    return render_template('admin/dashboard.html', stats=stats)

# Doctor Management Routes

@bp.route('/doctors')
@login_required
@admin_required
def doctors():
    """View all doctors"""
    doctors = Doctor.query.order_by(Doctor.created_at.desc()).all()
    return render_template('admin/doctors.html', doctors=doctors)

@bp.route('/doctors/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    """Add a new doctor"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        specialization_id = request.form.get('specialization_id')
        contact = request.form.get('contact')

        # Validation
        if not all([name, email, specialization_id]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('admin.add_doctor'))

        # Check if email already exists
        if Doctor.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('admin.add_doctor'))

        # Generate random password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        # Create doctor
        doctor = Doctor(
            name=name,
            email=email,
            specialization_id=specialization_id,
            contact=contact
        )
        doctor.set_password(password)

        db.session.add(doctor)
        db.session.commit()

        # Send email with credentials
        try:
            msg = Message(
                'Your Doctor Account - Hospital Management System',
                recipients=[email]
            )
            msg.body = f"""
Hello Dr. {name},

Your doctor account has been created in the Hospital Management System.

Login Credentials:
Email: {email}
Password: {password}

Please login at: http://localhost:5000/auth/login

Best regards,
Hospital Management System
            """
            mail.send(msg)
            flash(f'Doctor added successfully! Login credentials sent to {email}', 'success')
        except Exception as e:
            flash(f'Doctor added but email failed to send. Password: {password}', 'warning')

        return redirect(url_for('admin.doctors'))

    departments = Department.query.all()
    return render_template('admin/add_doctor.html', departments=departments)

@bp.route('/doctors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(id):
    """Edit doctor details"""
    doctor = Doctor.query.get_or_404(id)

    if request.method == 'POST':
        doctor.name = request.form.get('name')
        doctor.email = request.form.get('email')
        doctor.specialization_id = request.form.get('specialization_id')
        doctor.contact = request.form.get('contact')

        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('admin.doctors'))

    departments = Department.query.all()
    return render_template('admin/edit_doctor.html', doctor=doctor, departments=departments)

@bp.route('/doctors/toggle-blacklist/<int:id>')
@login_required
@admin_required
def toggle_blacklist_doctor(id):
    """Toggle doctor blacklist status"""
    doctor = Doctor.query.get_or_404(id)
    doctor.is_blacklisted = not doctor.is_blacklisted
    db.session.commit()

    status = 'blacklisted' if doctor.is_blacklisted else 'activated'
    flash(f'Doctor {doctor.name} has been {status}.', 'success')
    return redirect(url_for('admin.doctors'))

@bp.route('/doctors/delete/<int:id>')
@login_required
@admin_required
def delete_doctor(id):
    """Delete a doctor"""
    doctor = Doctor.query.get_or_404(id)

    # Check if doctor has appointments
    if doctor.appointments.count() > 0:
        flash('Cannot delete doctor with existing appointments. Please blacklist instead.', 'danger')
        return redirect(url_for('admin.doctors'))

    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('admin.doctors'))

# Patient Management Routes

@bp.route('/patients')
@login_required
@admin_required
def patients():
    """View all patients"""
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('admin/patients.html', patients=patients)

@bp.route('/patients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_patient(id):
    """Edit patient details"""
    patient = Patient.query.get_or_404(id)

    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.email = request.form.get('email')
        patient.contact = request.form.get('contact')

        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('admin.patients'))

    return render_template('admin/edit_patient.html', patient=patient)

@bp.route('/patients/toggle-blacklist/<int:id>')
@login_required
@admin_required
def toggle_blacklist_patient(id):
    """Toggle patient blacklist status"""
    patient = Patient.query.get_or_404(id)
    patient.is_blacklisted = not patient.is_blacklisted
    db.session.commit()

    status = 'blacklisted' if patient.is_blacklisted else 'activated'
    flash(f'Patient {patient.name} has been {status}.', 'success')
    return redirect(url_for('admin.patients'))

# Appointment Management Routes

@bp.route('/appointments')
@login_required
@admin_required
def appointments():
    """View all appointments"""
    status_filter = request.args.get('status', 'all')

    if status_filter == 'all':
        appointments = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    else:
        appointments = Appointment.query.filter_by(status=status_filter).order_by(
            Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template('admin/appointments.html', appointments=appointments, status_filter=status_filter)

# Search Routes

@bp.route('/search', methods=['GET', 'POST'])
@login_required
@admin_required
def search():
    """Search for patients and doctors"""
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        query = request.form.get('query')

        if search_type == 'patient':
            results = Patient.query.filter(
                (Patient.name.ilike(f'%{query}%')) |
                (Patient.email.ilike(f'%{query}%')) |
                (Patient.contact.ilike(f'%{query}%'))
            ).all()
            return render_template('admin/search.html', results=results, search_type='patient', query=query)

        elif search_type == 'doctor':
            results = Doctor.query.join(Department).filter(
                (Doctor.name.ilike(f'%{query}%')) |
                (Doctor.email.ilike(f'%{query}%')) |
                (Department.department_name.ilike(f'%{query}%'))
            ).all()
            return render_template('admin/search.html', results=results, search_type='doctor', query=query)

    return render_template('admin/search.html', results=None)
