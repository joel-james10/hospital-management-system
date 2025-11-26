"""
Doctor routes - dashboard, appointments, treatments, availability
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.appointment import Appointment
from models.treatment import Treatment
from models.doctor_availability import DoctorAvailability
from utils.decorators import doctor_required
from datetime import datetime, timedelta

bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@bp.route('/dashboard')
@login_required
@doctor_required
def dashboard():
    """Doctor dashboard with appointment overview"""
    today = datetime.now().date()

    # Get today's appointments
    today_appointments = Appointment.query.filter_by(
        doctor_id=current_user.id,
        date=today
    ).order_by(Appointment.time).all()

    # Get upcoming appointments (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.date > today,
        Appointment.date <= next_week
    ).order_by(Appointment.date, Appointment.time).all()

    stats = {
        'today': len(today_appointments),
        'upcoming': len(upcoming_appointments),
        'pending': Appointment.query.filter_by(
            doctor_id=current_user.id,
            status='Booked'
        ).count()
    }

    return render_template('doctor/dashboard.html',
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         stats=stats)

# Appointment Management Routes

@bp.route('/appointments')
@login_required
@doctor_required
def appointments():
    """View all appointments"""
    status_filter = request.args.get('status', 'all')

    if status_filter == 'all':
        appointments = Appointment.query.filter_by(
            doctor_id=current_user.id
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    else:
        appointments = Appointment.query.filter_by(
            doctor_id=current_user.id,
            status=status_filter
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    return render_template('doctor/appointments.html',
                         appointments=appointments,
                         status_filter=status_filter)

@bp.route('/appointments/view/<int:id>')
@login_required
@doctor_required
def view_appointment(id):
    """View detailed appointment information"""
    appointment = Appointment.query.get_or_404(id)

    # Ensure doctor can only view their own appointments
    if appointment.doctor_id != current_user.id:
        flash('You do not have permission to view this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))

    # Get all treatments for this appointment
    treatments = Treatment.query.filter_by(appointment_id=id).order_by(Treatment.created_at.desc()).all()

    # Get patient's medical history (all past treatments)
    patient_history = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == appointment.patient_id,
        Treatment.appointment_id != id
    ).order_by(Treatment.created_at.desc()).limit(5).all()

    return render_template('doctor/view_appointment.html',
                         appointment=appointment,
                         treatments=treatments,
                         patient_history=patient_history)

@bp.route('/appointments/complete/<int:id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def complete_appointment(id):
    """Complete appointment and add treatment"""
    appointment = Appointment.query.get_or_404(id)

    # Ensure doctor can only modify their own appointments
    if appointment.doctor_id != current_user.id:
        flash('You do not have permission to modify this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))

    # Check if appointment is already completed
    if appointment.status == 'Completed':
        flash('This appointment is already completed.', 'info')
        return redirect(url_for('doctor.view_appointment', id=id))

    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')

        if not diagnosis:
            flash('Diagnosis is required.', 'danger')
            return redirect(url_for('doctor.complete_appointment', id=id))

        # Create treatment record
        treatment = Treatment(
            appointment_id=id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )

        # Mark appointment as completed
        appointment.status = 'Completed'

        db.session.add(treatment)
        db.session.commit()

        flash('Appointment completed successfully!', 'success')
        return redirect(url_for('doctor.view_appointment', id=id))

    return render_template('doctor/complete_appointment.html', appointment=appointment)

@bp.route('/appointments/cancel/<int:id>')
@login_required
@doctor_required
def cancel_appointment(id):
    """Cancel an appointment"""
    appointment = Appointment.query.get_or_404(id)

    # Ensure doctor can only cancel their own appointments
    if appointment.doctor_id != current_user.id:
        flash('You do not have permission to cancel this appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))

    # Check if appointment can be cancelled
    if appointment.status == 'Completed':
        flash('Cannot cancel a completed appointment.', 'danger')
        return redirect(url_for('doctor.appointments'))

    appointment.status = 'Cancelled'
    db.session.commit()

    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('doctor.appointments'))

# Patient History Routes

@bp.route('/patients')
@login_required
@doctor_required
def patients():
    """View all patients with appointments"""
    # Get unique patients from appointments
    patients_with_appointments = db.session.query(
        Appointment.patient_id
    ).filter_by(doctor_id=current_user.id).distinct().all()

    patient_ids = [p[0] for p in patients_with_appointments]

    from models.patient import Patient
    patients = Patient.query.filter(Patient.id.in_(patient_ids)).all()

    return render_template('doctor/patients.html', patients=patients)

@bp.route('/patients/history/<int:patient_id>')
@login_required
@doctor_required
def patient_history(patient_id):
    """View complete medical history for a patient"""
    from models.patient import Patient
    patient = Patient.query.get_or_404(patient_id)

    # Verify doctor has treated this patient
    has_appointment = Appointment.query.filter_by(
        doctor_id=current_user.id,
        patient_id=patient_id
    ).first()

    if not has_appointment:
        flash('You do not have permission to view this patient.', 'danger')
        return redirect(url_for('doctor.patients'))

    # Get all appointments and treatments for this patient with current doctor
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id,
        patient_id=patient_id
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    # Get all treatments
    treatments = Treatment.query.join(Appointment).filter(
        Appointment.doctor_id == current_user.id,
        Appointment.patient_id == patient_id
    ).order_by(Treatment.created_at.desc()).all()

    return render_template('doctor/patient_history.html',
                         patient=patient,
                         appointments=appointments,
                         treatments=treatments)

# Availability Management Routes

@bp.route('/availability', methods=['GET', 'POST'])
@login_required
@doctor_required
def manage_availability():
    """Manage doctor's weekly availability schedule"""
    if request.method == 'POST':
        # Delete existing availability
        DoctorAvailability.query.filter_by(doctor_id=current_user.id).delete()

        # Process form data for each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for day in days:
            is_available = request.form.get(f'{day}_available') == 'on'

            if is_available:
                start_time = request.form.get(f'{day}_start')
                end_time = request.form.get(f'{day}_end')

                if start_time and end_time:
                    availability = DoctorAvailability(
                        doctor_id=current_user.id,
                        day_of_week=day,
                        start_time=datetime.strptime(start_time, '%H:%M').time(),
                        end_time=datetime.strptime(end_time, '%H:%M').time()
                    )
                    db.session.add(availability)

        db.session.commit()
        flash('Availability updated successfully!', 'success')
        return redirect(url_for('doctor.manage_availability'))

    # Get current availability
    availability = DoctorAvailability.query.filter_by(
        doctor_id=current_user.id
    ).all()

    # Create a dictionary for easy template access
    availability_dict = {slot.day_of_week: slot for slot in availability}

    return render_template('doctor/availability.html', availability=availability_dict)
