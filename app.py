from flask import Flask, render_template, redirect, url_for
from config import Config
from extensions import db, login_manager, mail

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail.init_app(app)

# Import models (will be created later)
# This import must come after db initialization
from models import admin, doctor, patient, department, appointment, treatment

# Import routes
from routes import auth, admin as admin_routes, doctor as doctor_routes, patient as patient_routes

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(admin_routes.bp)
app.register_blueprint(doctor_routes.bp)
app.register_blueprint(patient_routes.bp)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    # Try to load from each user type
    from models.admin import Admin
    from models.doctor import Doctor
    from models.patient import Patient

    # Check which type of user it is based on ID format
    # Format: <type>_<id> (e.g., "admin_1", "doctor_5", "patient_10")
    if user_id.startswith('admin_'):
        return Admin.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('doctor_'):
        return Doctor.query.get(int(user_id.split('_')[1]))
    elif user_id.startswith('patient_'):
        return Patient.query.get(int(user_id.split('_')[1]))
    return None

# Home route
@app.route('/')
def index():
    """Home page - redirect to login"""
    return redirect(url_for('auth.login'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
