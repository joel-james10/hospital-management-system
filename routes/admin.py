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
