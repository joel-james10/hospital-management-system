"""
Custom decorators for role-based access control
"""
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(allowed_roles):
    """
    Decorator to restrict access to specific roles
    Usage: @role_required(['admin', 'doctor'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('auth.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to restrict access to admins only"""
    return role_required(['admin'])(f)

def doctor_required(f):
    """Decorator to restrict access to doctors only"""
    return role_required(['doctor'])(f)

def patient_required(f):
    """Decorator to restrict access to patients only"""
    return role_required(['patient'])(f)
