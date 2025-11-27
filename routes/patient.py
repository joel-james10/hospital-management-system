"""
Patient routes - dashboard, doctor search, appointment booking, medical history
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.doctor import Doctor
from models.appointment import Appointment
from models.department import Department
from models.treatment import Treatment
from utils.decorators import patient_required
from datetime import datetime, timedelta

bp = Blueprint('patient', __name__, url_prefix='/patient')

@bp.route('/dashboard')
@login_required
@patient_required
def dashboard():
    """Patient dashboard with upcoming appointments and departments"""
    # Get all departments
    departments = Department.query.all()

    # Get upcoming appointments
    today = datetime.now().date()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.date >= today
    ).order_by(Appointment.date, Appointment.time).limit(5).all()

    stats = {
        'upcoming': len(upcoming_appointments),
        'total_doctors': Doctor.query.filter_by(is_blacklisted=False).count(),
        'departments': len(departments)
    }

    return render_template('patient/dashboard.html',
                         departments=departments,
                         upcoming_appointments=upcoming_appointments,
                         stats=stats)

# Doctor Search and Viewing Routes

@bp.route('/doctors')
@login_required
@patient_required
def find_doctors():
    """Search and find doctors"""
    specialization_id = request.args.get('specialization', type=int)

    if specialization_id:
        doctors = Doctor.query.filter_by(
            specialization_id=specialization_id,
            is_blacklisted=False
        ).all()
    else:
        doctors = Doctor.query.filter_by(is_blacklisted=False).all()

    departments = Department.query.all()

    return render_template('patient/find_doctors.html',
                         doctors=doctors,
                         departments=departments,
                         selected_specialization=specialization_id)

@bp.route('/doctors/<int:doctor_id>')
@login_required
@patient_required
def view_doctor(doctor_id):
    """View doctor profile and availability"""
    doctor = Doctor.query.get_or_404(doctor_id)

    if doctor.is_blacklisted:
        flash('This doctor is not available.', 'danger')
        return redirect(url_for('patient.find_doctors'))

    # Get doctor's availability
    from models.doctor_availability import DoctorAvailability
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()

    return render_template('patient/view_doctor.html',
                         doctor=doctor,
                         availability=availability)

# Appointment Management Routes

@bp.route('/appointments')
@login_required
@patient_required
def appointments():
    """View all appointments"""
    status_filter = request.args.get('status', 'all')

    if status_filter == 'all':
        appointments = Appointment.query.filter_by(
            patient_id=current_user.id
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    else:
        appointments = Appointment.query.filter_by(
            patient_id=current_user.id,
            status=status_filter
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template('patient/appointments.html',
                         appointments=appointments,
                         status_filter=status_filter)

@bp.route('/appointments/book/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment(doctor_id):
    """Book an appointment with a doctor"""
    doctor = Doctor.query.get_or_404(doctor_id)

    if doctor.is_blacklisted:
        flash('This doctor is not available.', 'danger')
        return redirect(url_for('patient.find_doctors'))

    if request.method == 'POST':
        appointment_date = request.form.get('date')
        appointment_time = request.form.get('time')

        if not all([appointment_date, appointment_time]):
            flash('Please select both date and time.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

        # Convert to proper formats
        apt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        apt_time = datetime.strptime(appointment_time, '%H:%M').time()

        # Validation: Check if date is in the past
        if apt_date < datetime.now().date():
            flash('Cannot book appointments in the past.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

        # Validation: Check for conflicting appointments
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=apt_date,
            time=apt_time
        ).filter(Appointment.status != 'Cancelled').first()

        if existing:
            flash('This time slot is already booked. Please choose another time.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

        # Validation: Check doctor availability
        from models.doctor_availability import DoctorAvailability
        day_name = apt_date.strftime('%A')
        availability = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            day_of_week=day_name
        ).first()

        if not availability:
            flash(f'Doctor is not available on {day_name}s.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

        if not (availability.start_time <= apt_time <= availability.end_time):
            flash('Selected time is outside doctor\'s available hours.', 'danger')
            return redirect(url_for('patient.book_appointment', doctor_id=doctor_id))

        # Create appointment
        appointment = Appointment(
            patient_id=current_user.id,
            doctor_id=doctor_id,
            date=apt_date,
            time=apt_time,
            status='Booked'
        )

        db.session.add(appointment)
        db.session.commit()

        flash(f'Appointment booked successfully with Dr. {doctor.name} on {apt_date} at {apt_time.strftime("%I:%M %p")}!', 'success')
        return redirect(url_for('patient.appointments'))

    # Get doctor's availability for the form
    from models.doctor_availability import DoctorAvailability
    availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()

    # Calculate minimum booking date (1 day in advance)
    min_date = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')

    return render_template('patient/book_appointment.html',
                         doctor=doctor,
                         availability=availability,
                         min_date=min_date)

@bp.route('/appointments/cancel/<int:id>')
@login_required
@patient_required
def cancel_appointment(id):
    """Cancel an appointment"""
    appointment = Appointment.query.get_or_404(id)

    # Ensure patient can only cancel their own appointments
    if appointment.patient_id != current_user.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('patient.appointments'))

    # Check if appointment can be cancelled
    if appointment.status == 'Completed':
        flash('Cannot cancel a completed appointment.', 'danger')
        return redirect(url_for('patient.appointments'))

    if appointment.status == 'Cancelled':
        flash('This appointment is already cancelled.', 'info')
        return redirect(url_for('patient.appointments'))

    appointment.status = 'Cancelled'
    db.session.commit()

    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('patient.appointments'))

# Medical History Routes

@bp.route('/history')
@login_required
@patient_required
def medical_history():
    """View complete medical history"""
    # Get all completed appointments with treatments
    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    # Get all treatments
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == current_user.id
    ).order_by(Treatment.created_at.desc()).all()

    return render_template('patient/medical_history.html',
                         appointments=appointments,
                         treatments=treatments)
