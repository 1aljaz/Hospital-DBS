from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(role=None):
    """
    Decorator to protect routes based on login status and optional role.

    Usage:
        @login_required()             # any logged-in user
        @login_required(role="admin") # only admin users
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Login required", "warning")
                return redirect(url_for("auth.login"))
            if role and session.get("role") != role:
                flash("Access denied", "danger")
                return redirect(url_for("main.index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
