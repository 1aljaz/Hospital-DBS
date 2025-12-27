from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from app.decorators import roles_required
from app.models import Appointment, Admission, Diagnosis, Staff, Patient, Bed
from app.db import db
from datetime import datetime

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html", user=current_user)

@main_bp.route("/login", methods=["GET", "POST"])
def login_redirect():
    """Redirect /login to /auth/ for backward compatibility"""
    return redirect(url_for("auth.login"))

@main_bp.route("/admin")
@login_required
@roles_required("admin")
def admin_dashboard():
    return "admin dashboard"

@main_bp.route("/doctor")
@login_required
@roles_required("doctor")
def doctor_dashboard():
    return render_template("home_doctor.html", user=current_user)

@main_bp.route("/patient")
@login_required
@roles_required("patient")
def patient_dashboard():
    return "patient dashboard"

# Doctor routes
@main_bp.route("/appointment_doctor")
@login_required
@roles_required("doctor")
def appointment_doctor():
    # Get the staff_id for the current doctor
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    staff_id = staff.staff_id
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    # Query appointments for this doctor
    query = Appointment.query.filter_by(staff_id=staff_id)
    
    # Apply search filter (by patient name or ID)
    if search:
        try:
            # Try to search by patient ID
            patient_id = int(search)
            query = query.filter_by(patient_id=patient_id)
        except ValueError:
            # Search by patient name (via User relationship)
            from app.models.user import User
            query = query.join(Patient).join(User).filter(User.name.ilike(f'%{search}%'))
    
    # Apply status filter
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    # Prepare data for template
    data_rows = []
    for apt in appointments:
        patient = Patient.query.get(apt.patient_id)
        patient_name = f'Patient {apt.patient_id}'
        if patient and patient.user:
            patient_name = patient.user.name
        data_rows.append({
            'appointment_id': apt.appointment_id,
            'patient_id': apt.patient_id,
            'patient_name': patient_name,
            'appointment_date': apt.appointment_date,
            'appointment_time': apt.appointment_time,
            'status': apt.status or 'pending'
        })
    
    return render_template("appointment_doctor.html", data_rows=data_rows, user=current_user)

@main_bp.route("/admission_doctor")
@login_required
@roles_required("doctor")
def admission_doctor():
    # Get search parameter
    search = request.args.get('search', '').strip()
    
    # Query all admissions
    query = Admission.query
    
    # Apply search filter
    if search:
        try:
            # Try to search by patient ID or bed ID
            search_id = int(search)
            query = query.filter(
                (Admission.patient_id == search_id) | (Admission.bed_id == search_id)
            )
        except ValueError:
            # If not a number, search by patient name (via User relationship)
            from app.models.user import User
            query = query.join(Patient).join(User).filter(User.name.ilike(f'%{search}%'))
    
    admissions = query.order_by(Admission.admitted_date.desc()).all()
    
    # Prepare data for template
    admission_rows = []
    for adm in admissions:
        patient = Patient.query.get(adm.patient_id)
        patient_name = f'Patient {adm.patient_id}'
        if patient and patient.user:
            patient_name = patient.user.name
        
        bed = Bed.query.get(adm.bed_id)
        bed_info = f'Bed {adm.bed_id}'
        if bed:
            bed_info = f'Postelja {adm.bed_id} (Soba {bed.room_id})'
        
        admission_rows.append({
            'admission_id': adm.admission_id,
            'patient_id': adm.patient_id,
            'patient_name': patient_name,
            'bed_id': adm.bed_id,
            'bed_info': bed_info,
            'admitted_date': adm.admitted_date,
            'discharged_date': adm.discharged_date
        })
    
    return render_template("admission_doctor.html", admission_rows=admission_rows, user=current_user)

@main_bp.route("/diagnosis_doctor")
@login_required
@roles_required("doctor")
def diagnosis_doctor():
    # Get the staff_id for the current doctor
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    staff_id = staff.staff_id
    
    # Get search parameter
    search = request.args.get('search', '').strip()
    
    # Query diagnoses for appointments belonging to this doctor
    query = Diagnosis.query.join(Appointment).filter(Appointment.staff_id == staff_id)
    
    # Apply search filter
    if search:
        try:
            # Try to search by appointment ID
            appointment_id = int(search)
            query = query.filter(Diagnosis.appointment_id == appointment_id)
        except ValueError:
            # Search by description
            query = query.filter(Diagnosis.description.ilike(f'%{search}%'))
    
    diagnoses = query.order_by(Diagnosis.diagnosis_id.desc()).all()
    
    # Prepare data for template
    diagnosis_rows = []
    for diag in diagnoses:
        diagnosis_rows.append({
            'diagnosis_id': diag.diagnosis_id,
            'appointment_id': diag.appointment_id,
            'description': diag.description
        })
    
    return render_template("diagnosis_doctor.html", diagnosis_rows=diagnosis_rows, user=current_user)

# CRUD Operations for Appointments
@main_bp.route("/add_appointment", methods=["GET", "POST"])
@login_required
@roles_required("doctor")
def add_appointment():
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    if request.method == "POST":
        try:
            patient_id = int(request.form.get('patient_id'))
            appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
            appointment_time = datetime.strptime(request.form.get('appointment_time'), '%H:%M').time()
            status = request.form.get('status', 'pending')
            
            appointment = Appointment(
                patient_id=patient_id,
                staff_id=staff.staff_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=status
            )
            db.session.add(appointment)
            db.session.commit()
            flash("Pregled uspešno dodan", "success")
            return redirect(url_for("main.appointment_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju pregleda: {str(e)}", "danger")
    
    # Get all patients for dropdown
    patients = Patient.query.join(Patient.user).all()
    return render_template("add_appointment.html", patients=patients, user=current_user)

@main_bp.route("/update_appointment/<int:appointment_id>", methods=["GET", "POST"])
@login_required
@roles_required("doctor")
def update_appointment(appointment_id):
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify the appointment belongs to this doctor
    if appointment.staff_id != staff.staff_id:
        flash("Nimate dostopa do tega pregleda", "danger")
        return redirect(url_for("main.appointment_doctor"))
    
    if request.method == "POST":
        try:
            appointment.patient_id = int(request.form.get('patient_id'))
            appointment.appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
            appointment.appointment_time = datetime.strptime(request.form.get('appointment_time'), '%H:%M').time()
            appointment.status = request.form.get('status', 'pending')
            
            db.session.commit()
            flash("Pregled uspešno posodobljen", "success")
            return redirect(url_for("main.appointment_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju pregleda: {str(e)}", "danger")
    
    # Get all patients for dropdown
    patients = Patient.query.join(Patient.user).all()
    return render_template("update_appointment.html", appointment=appointment, patients=patients, user=current_user)

@main_bp.route("/delete_appointment/<int:appointment_id>", methods=["POST"])
@login_required
@roles_required("doctor")
def delete_appointment(appointment_id):
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verify the appointment belongs to this doctor
    if appointment.staff_id != staff.staff_id:
        flash("Nimate dostopa do tega pregleda", "danger")
        return redirect(url_for("main.appointment_doctor"))
    
    try:
        db.session.delete(appointment)
        db.session.commit()
        flash("Pregled uspešno izbrisan", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Napaka pri brisanju pregleda: {str(e)}", "danger")
    
    return redirect(url_for("main.appointment_doctor"))

# CRUD Operations for Diagnoses
@main_bp.route("/add_diagnosis", methods=["GET", "POST"])
@login_required
@roles_required("doctor")
def add_diagnosis():
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    if request.method == "POST":
        try:
            appointment_id = int(request.form.get('appointment_id'))
            description = request.form.get('description', '').strip()
            
            # Verify the appointment belongs to this doctor
            appointment = Appointment.query.get_or_404(appointment_id)
            if appointment.staff_id != staff.staff_id:
                flash("Nimate dostopa do tega pregleda", "danger")
                return redirect(url_for("main.add_diagnosis"))
            
            diagnosis = Diagnosis(
                appointment_id=appointment_id,
                description=description
            )
            db.session.add(diagnosis)
            db.session.commit()
            flash("Diagnoza uspešno dodana", "success")
            return redirect(url_for("main.diagnosis_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju diagnoze: {str(e)}", "danger")
    
    # Get appointments for this doctor
    appointments = Appointment.query.filter_by(staff_id=staff.staff_id).all()
    return render_template("add_diagnosis.html", appointments=appointments, user=current_user)

@main_bp.route("/update_diagnosis/<int:diagnosis_id>", methods=["GET", "POST"])
@login_required
@roles_required("doctor")
def update_diagnosis(diagnosis_id):
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    
    # Verify the diagnosis belongs to an appointment of this doctor
    appointment = Appointment.query.get_or_404(diagnosis.appointment_id)
    if appointment.staff_id != staff.staff_id:
        flash("Nimate dostopa do te diagnoze", "danger")
        return redirect(url_for("main.diagnosis_doctor"))
    
    if request.method == "POST":
        try:
            diagnosis.description = request.form.get('description', '').strip()
            
            db.session.commit()
            flash("Diagnoza uspešno posodobljena", "success")
            return redirect(url_for("main.diagnosis_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju diagnoze: {str(e)}", "danger")
    
    return render_template("update_diagnosis.html", diagnosis=diagnosis, user=current_user)

@main_bp.route("/delete_diagnosis/<int:diagnosis_id>", methods=["POST"])
@login_required
@roles_required("doctor")
def delete_diagnosis(diagnosis_id):
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    
    # Verify the diagnosis belongs to an appointment of this doctor
    appointment = Appointment.query.get_or_404(diagnosis.appointment_id)
    if appointment.staff_id != staff.staff_id:
        flash("Nimate dostopa do te diagnoze", "danger")
        return redirect(url_for("main.diagnosis_doctor"))
    
    try:
        db.session.delete(diagnosis)
        db.session.commit()
        flash("Diagnoza uspešno izbrisana", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Napaka pri brisanju diagnoze: {str(e)}", "danger")
    
    return redirect(url_for("main.diagnosis_doctor"))

# CRUD Operations for Admissions
@main_bp.route("/update_admission/<int:admission_id>", methods=["GET", "POST"])
@login_required
@roles_required("doctor")
def update_admission(admission_id):
    admission = Admission.query.get_or_404(admission_id)
    
    if request.method == "POST":
        try:
            admission.patient_id = int(request.form.get('patient_id'))
            admission.bed_id = int(request.form.get('bed_id'))
            admission.admitted_date = datetime.strptime(request.form.get('admitted_date'), '%Y-%m-%d').date()
            
            discharged_date_str = request.form.get('discharged_date', '').strip()
            if discharged_date_str:
                admission.discharged_date = datetime.strptime(discharged_date_str, '%Y-%m-%d').date()
            else:
                admission.discharged_date = None
            
            db.session.commit()
            flash("Sprejem uspešno posodobljen", "success")
            return redirect(url_for("main.admission_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju sprejema: {str(e)}", "danger")
    
    # Get all patients and beds for dropdowns
    patients = Patient.query.join(Patient.user).all()
    beds = Bed.query.all()
    return render_template("update_admission.html", admission=admission, patients=patients, beds=beds, user=current_user)




