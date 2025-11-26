from datetime import datetime
from extensions import db

class Department(db.Model):
    """Department/Specialization model"""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    doctors = db.relationship('Doctor', backref='department_rel', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.department_name}>'
