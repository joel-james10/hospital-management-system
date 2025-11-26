"""
Flask extensions initialization
Separate file to avoid circular imports
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Initialize extensions (without app)
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
