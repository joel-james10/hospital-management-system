from datetime import datetime
from extensions import db

class DoctorAvailability(db.Model):
    """Doctor Availability model - store doctor weekly recurring schedule"""
    __tablename__ = 'doctor_availability'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique constraint to prevent duplicate day slots
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'day_of_week', name='unique_doctor_day'),
    )

    def __repr__(self):
        return f'<DoctorAvailability Doctor:{self.doctor_id} {self.day_of_week} {self.start_time}-{self.end_time}>'
