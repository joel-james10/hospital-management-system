from datetime import datetime
from extensions import db

class DoctorAvailability(db.Model):
    """Doctor Availability model - store doctor time slots for next 7 days"""
    __tablename__ = 'doctor_availability'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)  # Format: "09:00", "10:00", etc.
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique constraint to prevent duplicate slots
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'date', 'time_slot', name='unique_doctor_slot'),
    )

    def __repr__(self):
        return f'<DoctorAvailability Doctor:{self.doctor_id} {self.date} {self.time_slot}>'
