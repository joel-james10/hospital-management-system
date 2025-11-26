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
