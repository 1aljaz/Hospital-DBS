from flask import Blueprint, request, redirect, url_for, render_template, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.db import db
from app.models.user import User
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# LOGIN page
@auth_bp.route("/", methods=["GET", "POST"])
def login():
    # Redirect if already logged in
    if current_user.is_authenticated:
        if current_user.role.value == "admin":
            return redirect(url_for("main.admin_dashboard"))
        elif current_user.role.value == "doctor":
            return redirect(url_for("main.doctor_dashboard"))
        else:
            return redirect(url_for("main.index"))
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        print(f"Login attempt for username: {username}")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            print(f"Password check passed for user: {user.user_id}, role: {user.role.value}")
            result = login_user(user, remember=True)
            print(f"login_user result: {result}, user_id: {user.get_id()}")
            print(f"Session after login: {dict(session)}")
            print(f"Current user authenticated: {current_user.is_authenticated}")
            flash(f"Logged in as {user.role.value}", "success")
            print(f"{user} succesfully logged in.")
            
            # Get the next URL from Flask-Login if available
            next_url = request.args.get('next')
            if next_url:
                print(f"Redirecting to next URL: {next_url}")
                return redirect(next_url)
            
            if user.role.value == "admin":
                target_url = url_for("main.admin_dashboard")
                print(f"Redirecting to admin dashboard: {target_url}")
                return redirect(target_url)
            elif user.role.value == "doctor":
                target_url = url_for("main.doctor_dashboard")
                print(f"Redirecting to doctor dashboard: {target_url}")
                return redirect(target_url)
            else:
                target_url = url_for("main.index")
                print(f"Redirecting to main index: {target_url}")
                return redirect(target_url)

        else:
            print("Invalid username or password")
            flash("Invalid username or password", "danger")
    print(2)
    return render_template("index.html")

# LOGOUT
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for("main.index"))
