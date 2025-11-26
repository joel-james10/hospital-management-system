"""
Database initialization script
Creates all tables and seeds initial data
"""
from app import app
from extensions import db
from models.admin import Admin
from models.department import Department
from models.doctor import Doctor
from models.patient import Patient
from config import Config
from datetime import date

def init_database():
    """Initialize database with tables and seed data"""
    with app.app_context():
        # Drop all existing tables (for development)
        print("Dropping existing tables...")
        db.drop_all()

        # Create all tables
        print("Creating database tables...")
        db.create_all()

        # Create predefined admin user
        print("Creating admin user...")
        admin = Admin(
            username=Config.ADMIN_USERNAME,
            email=Config.ADMIN_EMAIL,
            is_active=True
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        db.session.add(admin)

        # Create sample departments/specializations
        print("Creating departments...")
        departments = [
            Department(department_name='General Medicine', description='General medical consultation and treatment'),
            Department(department_name='Cardiology', description='Heart and cardiovascular system'),
            Department(department_name='Orthopedics', description='Bone, joint, and muscle treatment'),
            Department(department_name='Pediatrics', description='Medical care for infants, children, and adolescents'),
            Department(department_name='Dermatology', description='Skin, hair, and nail treatment'),
            Department(department_name='Neurology', description='Brain and nervous system'),
            Department(department_name='Gynecology', description='Women\'s reproductive health'),
            Department(department_name='Ophthalmology', description='Eye care and vision'),
        ]

        for dept in departments:
            db.session.add(dept)

        # Commit departments first so we can reference them
        db.session.commit()

        # Create sample doctors (optional - for testing)
        print("Creating sample doctors...")
        sample_doctors = [
            {
                'name': 'Dr. Sarah Johnson',
                'email': 'sarah.johnson@hospital.com',
                'specialization_id': 1,  # General Medicine
                'contact': '555-0101'
            },
            {
                'name': 'Dr. Michael Chen',
                'email': 'michael.chen@hospital.com',
                'specialization_id': 2,  # Cardiology
                'contact': '555-0102'
            },
            {
                'name': 'Dr. Emily Rodriguez',
                'email': 'emily.rodriguez@hospital.com',
                'specialization_id': 4,  # Pediatrics
                'contact': '555-0103'
            },
        ]

        for doc_data in sample_doctors:
            doctor = Doctor(
                name=doc_data['name'],
                email=doc_data['email'],
                specialization_id=doc_data['specialization_id'],
                contact=doc_data['contact']
            )
            doctor.set_password('doctor123')  # Default password for testing
            db.session.add(doctor)

        # Create sample patient (optional - for testing)
        print("Creating sample patient...")
        patient = Patient(
            name='John Doe',
            email='john.doe@example.com',
            contact='555-0201',
            date_of_birth=date(1990, 5, 15)
        )
        patient.set_password('patient123')  # Default password for testing
        db.session.add(patient)

        # Commit all changes
        db.session.commit()

        print("\n[SUCCESS] Database initialized successfully!")
        print(f"\nAdmin Credentials:")
        print(f"  Username: {Config.ADMIN_USERNAME}")
        print(f"  Email: {Config.ADMIN_EMAIL}")
        print(f"  Password: {Config.ADMIN_PASSWORD}")
        print(f"\nSample Doctor Credentials (for testing):")
        print(f"  Email: sarah.johnson@hospital.com")
        print(f"  Password: doctor123")
        print(f"\nSample Patient Credentials (for testing):")
        print(f"  Email: john.doe@example.com")
        print(f"  Password: patient123")

if __name__ == '__main__':
    init_database()
