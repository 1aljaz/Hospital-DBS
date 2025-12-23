from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.db import db
from app.models.user import User, RoleEnum
from app.routes.main import main_bp
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# LOGIN page (GET + POST)
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.user_id
            session["role"] = user.role.value  
            flash(f"Logged in as {user.role.value}", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("main.index"))
