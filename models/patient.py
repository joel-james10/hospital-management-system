from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class Patient(UserMixin, db.Model):
    """Patient model - self-registration allowed"""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return unique ID for Flask-Login"""
        return f'patient_{self.id}'

    @property
    def role(self):
        """Return user role"""
        return 'patient'

    def __repr__(self):
        return f'<Patient {self.name}>'
