from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class Doctor(UserMixin, db.Model):
    """Doctor model - added by admin only"""
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    contact = db.Column(db.String(20))
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')
    availability_slots = db.relationship('DoctorAvailability', backref='doctor', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return unique ID for Flask-Login"""
        return f'doctor_{self.id}'

    @property
    def role(self):
        """Return user role"""
        return 'doctor'

    @property
    def specialization(self):
        """Get specialization name"""
        return self.department_rel.department_name if self.department_rel else None

    def __repr__(self):
        return f'<Doctor {self.name}>'
