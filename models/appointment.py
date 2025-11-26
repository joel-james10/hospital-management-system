from datetime import datetime
from extensions import db

class Appointment(db.Model):
    """Appointment model - links patients and doctors with time slots"""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(10), nullable=False)  # Format: "09:00", "10:00", etc.
    status = db.Column(db.String(20), default='Booked')  # Booked / Completed / Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Appointment {self.id}: {self.date} {self.time} - {self.status}>'
