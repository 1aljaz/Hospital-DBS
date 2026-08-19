from flask import Blueprint, request, redirect, url_for, render_template
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
        if current_user.is_admin():
            return redirect(url_for("main.admin_dashboard"))
        elif current_user.is_doctor():
            return redirect(url_for("main.doctor_dashboard"))
        elif current_user.is_patient():
            return redirect(url_for("main.patient_dashboard"))
        else:
            return redirect(url_for("main.index"))
    
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            
            # Get the next URL from Flask-Login if available
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            
            if user.is_admin():
                target_url = url_for("main.admin_dashboard")
                return redirect(target_url)
            elif user.is_doctor():
                target_url = url_for("main.doctor_dashboard")
                return redirect(target_url)
            elif user.is_patient():
                target_url = url_for("main.patient_dashboard")
                return redirect(target_url)
            else:
                target_url = url_for("main.index")
                return redirect(target_url)

    return render_template("index.html")

# LOGOUT
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
