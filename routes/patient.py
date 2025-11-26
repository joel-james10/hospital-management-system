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
