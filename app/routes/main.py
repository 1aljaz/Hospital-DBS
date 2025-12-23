from flask import Blueprint
from app.routes.decorators import login_required

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return "Pozdravjeni, to je najin projekt za podatkovne baze 1."

@main_bp.route("/admin")
@login_required("admin")
def admin_dashboard():
    return "admin dashboard"

@main_bp.route("/doctor")
@login_required("doctor")
def doctor_dashboard():
    return "doctor dashboard"

@main_bp.route("/patient")
@login_required("patient")
def patient_dashboard():
    return "patient dashboard"




