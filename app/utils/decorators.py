"""Utility decorators for role-based access control."""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from app.models.user import UserRole


def role_required(*roles: UserRole):
    """Decorator that restricts access to users with specific roles."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                flash("You don't have permission to access this page.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def student_only(f):
    return role_required(UserRole.STUDENT)(f)


def admin_only(f):
    return role_required(UserRole.ADMIN)(f)
