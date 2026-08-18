from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required

def roles_required(*roles):
    """
    Decorator to restrict access based on user roles.
    Usage: @roles_required("ADMIN", "DOCTOR")
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role.value not in roles:
                return redirect(url_for("main.index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator
