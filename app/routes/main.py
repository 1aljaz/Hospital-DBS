from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from app.decorators import roles_required
from app.models import Appointment, Admission, Diagnosis, Staff, Patient, Bed, Department, Room
from app.models.user import User, RoleEnum
from app.db import db
from datetime import datetime
from werkzeug.security import generate_password_hash

main_bp = Blueprint("main", __name__)


def _delete_appointment_record(appointment):
    for diagnosis in list(appointment.diagnoses):
        db.session.delete(diagnosis)
    db.session.delete(appointment)


def _delete_patient_record(patient):
    for appointment in list(patient.appointments):
        _delete_appointment_record(appointment)
    for admission in list(patient.admissions):
        db.session.delete(admission)
    db.session.delete(patient)


def _delete_staff_record(staff):
    for appointment in list(staff.appointments):
        _delete_appointment_record(appointment)
    db.session.delete(staff)


def _delete_bed_record(bed):
    for admission in list(bed.admissions):
        db.session.delete(admission)
    db.session.delete(bed)


def _delete_room_record(room):
    for bed in list(room.beds):
        _delete_bed_record(bed)
    db.session.delete(room)


def _delete_department_record(department):
    for staff_member in list(department.staff_members):
        _delete_staff_record(staff_member)
    for room in list(department.rooms):
        _delete_room_record(room)
    db.session.delete(department)


def _delete_user_record(user):
    if user.patient:
        _delete_patient_record(user.patient)
    if user.staff:
        _delete_staff_record(user.staff)
    db.session.delete(user)


def _delete_record_and_redirect(action, success_message, error_message, redirect_url):
    try:
        action()
        db.session.commit()
        flash(success_message, "success")
    except Exception as e:
        db.session.rollback()
        flash(f"{error_message}: {str(e)}", "danger")
    return redirect(redirect_url)


def _redirect_for_role(staff, admin_endpoint, doctor_endpoint):
    if not staff:
        return url_for(admin_endpoint)
    return url_for(doctor_endpoint)


#za dobit html
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
    return render_template("home_admin.html", user=current_user)

@main_bp.route("/doctor")
@login_required
@roles_required("doctor")
def doctor_dashboard():
    return render_template("home_doctor.html", user=current_user)

@main_bp.route("/patient")
@login_required
@roles_required("patient")
def patient_dashboard():
    return render_template("home_patient.html", user=current_user)

# Doctor routes
@main_bp.route("/appointment_doctor")
@login_required
@roles_required("doctor")
def appointment_doctor():
    # Dobiš staff id od zdravnika
    staff = current_user.staff
    if not staff:
        staff = Staff.query.filter_by(user_id=current_user.user_id).first()
        if not staff:
            staff = Staff(user_id=current_user.user_id, role="doctor")
            db.session.add(staff)
            db.session.commit()
        else:
            current_user.staff = staff
    
    if not staff:
        return "Error: No staff record found", 404
    
    staff_id = staff.staff_id
    
    # Dobiš parametre za search pa filter
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    # query appointmentovza tega zdravnika 
    query = Appointment.query.filter_by(staff_id=staff_id)
    
    # searchaj
    if search:
        try:
            #po id
            patient_id = int(search)
            query = query.filter_by(patient_id=patient_id)
        except ValueError:
            #po imenu
            from app.models.user import User
            query = query.join(Patient).join(User).filter(User.name.ilike(f'%{search}%'))
    
    # uporabi filter za status
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    
    # priprava podatkov
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
    # param za search
    search = request.args.get('search', '').strip()
    query = Admission.query
    
    if search:
        try:
            search_id = int(search)
            query = query.filter(
                (Admission.patient_id == search_id) | (Admission.bed_id == search_id)
            )
        except ValueError:
            # If not a number, search by patient name (via User relationship)
            from app.models.user import User
            query = query.join(Patient).join(User).filter(User.name.ilike(f'%{search}%'))
    
    admissions = query.order_by(Admission.admitted_date.desc()).all()
    
    # pripravi podatke za template
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
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    staff_id = staff.staff_id
    
    search = request.args.get('search', '').strip()
    
    query = Diagnosis.query.join(Appointment).filter(Appointment.staff_id == staff_id)
    
    if search:
        try:
            appointment_id = int(search)
            query = query.filter(Diagnosis.appointment_id == appointment_id)
        except ValueError:
            # Searchaj po descriptionu
            query = query.filter(Diagnosis.description.ilike(f'%{search}%'))
    
    diagnoses = query.order_by(Diagnosis.diagnosis_id.desc()).all()

    diagnosis_rows = []
    for diag in diagnoses:
        diagnosis_rows.append({
            'diagnosis_id': diag.diagnosis_id,
            'appointment_id': diag.appointment_id,
            'description': diag.description
        })
    return render_template("diagnosis_doctor.html", diagnosis_rows=diagnosis_rows, user=current_user)

# CRUD za Departmente
@main_bp.route("/add_department", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_department():
    if request.method == "POST":
        try:
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            
            if not name or not location:
                flash("Vsa obvezna polja morajo biti izpolnjena", "danger")
                return render_template("add_department.html", user=current_user)
            
            department = Department(name=name, location=location)
            db.session.add(department)
            db.session.commit()
            flash("Odelek uspešno dodan", "success")
            return redirect(url_for("main.department_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju oddelka: {str(e)}", "danger")
    
    return render_template("add_department.html", user=current_user)

@main_bp.route("/update_department/<int:department_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_department(department_id):

    
    department = Department.query.get_or_404(department_id)
    
    if request.method == "POST":
        try:
            department.name = request.form.get('department_name')
            department.location = request.form.get('department_location')
            
            db.session.commit()
            flash("Oddelek uspešno posodobljen", "success")
            return redirect(url_for("main.department_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju oddelka: {str(e)}", "danger")
    

    return render_template("update_department.html", department=department, user=current_user)

@main_bp.route("/delete_department/<int:department_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    return _delete_record_and_redirect(
        lambda: _delete_department_record(department),
        "Oddelek uspešno izbrisan",
        "Napaka pri brisanju oddelka",
        url_for("main.department_admin")
    )


# CRUD Operations za Staff
# Dodaj stafd
@main_bp.route("/add_staff", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_staff():
    if request.method == "POST":
        try:
            name = request.form.get('name', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            role_str = request.form.get('role', '').strip()
            
            if not name or not username or not password or not role_str:
                flash("Vsa obvezna polja morajo biti izpolnjena", "danger")
                return render_template("add_staff.html", user=current_user)
            
            # if username obstaja
            if User.query.filter_by(username=username).first():
                flash("Uporabniško ime že obstaja", "danger")
                return render_template("add_staff.html", user=current_user)
            
            role = RoleEnum[role_str.upper()]
            password_hash = generate_password_hash(password)
            
            new_user = User(
                name=name,
                username=username,
                password_hash=password_hash,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()

            if role == RoleEnum.DOCTOR:
                # Doctor mora met depart.
                dept = Department.query.first()
                staff = Staff(user_id=new_user.user_id, role="doctor", department_id=dept.department_id if dept else None)
                db.session.add(staff)
                db.session.commit()
            
            flash("Uporabnik uspešno dodan", "success")
            return redirect(url_for("main.staff_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju uporabnika: {str(e)}", "danger")
    
    return render_template("add_staff.html", user=current_user)

# Update Staff
@main_bp.route("/update_staff/<int:staff_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    user = User.query.get_or_404(staff.user_id)
    if request.method == "POST":
        try:
            staff.role = request.form.get('role')
            staff.department_id = request.form.get('department_id')

            user.name = request.form.get('name', '').strip()

            db.session.commit()
            flash("Zaposleni uspešno posodobljen", "success")
            return redirect(url_for("main.staff_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju zaposlenega: {str(e)}", "danger")
    
    departments = Department.query.all()
    return render_template("update_staff.html", staff=staff, departments=departments, user=current_user)

# Delete Staff
@main_bp.route("/delete_staff/<int:staff_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    return _delete_record_and_redirect(
        lambda: _delete_staff_record(staff),
        "Zaposlenega uspešno izbrisan",
        "Napaka pri brisanju zaposlenega",
        url_for("main.staff_admin")
    )

@main_bp.route("/update_patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    if request.method == "POST":
        try:
            patient.gender = request.form.get('gender')
            patient.address = request.form.get('address')

            user.name = request.form.get('name', '').strip()

            db.session.commit()
            flash("Pacient uspešno posodobljen", "success")
            return redirect(url_for("main.patient_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju pacienta: {str(e)}", "danger")
    
    return render_template("update_patient.html", patient=patient, user=current_user)

@main_bp.route("/delete_patient/<int:patient_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return _delete_record_and_redirect(
        lambda: _delete_patient_record(patient),
        "Pacient uspešno izbrisan",
        "Napaka pri brisanju pacienta",
        url_for("main.patient_admin")
    )

# CRUD Operations za Appointmente
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
    
    # pacienti za dropdown
    patients = Patient.query.join(Patient.user).all()
    return render_template("add_appointment.html", patients=patients, user=current_user)

@main_bp.route("/add_appointment_admin", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_appointment_admin():
    
    if request.method == "POST":
        try:
            patient_id = int(request.form.get('patient_id'))
            doctor_id = int(request.form.get('staff_id'))
            appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
            appointment_time = datetime.strptime(request.form.get('appointment_time'), '%H:%M').time()
            status = request.form.get('status', 'pending')
            
            appointment = Appointment(
                patient_id=patient_id,
                staff_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status=status
            )
            db.session.add(appointment)
            db.session.commit()
            flash("Pregled uspešno dodan", "success")
            return redirect(url_for("main.appointment_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju pregleda: {str(e)}", "danger")
    
    
    patients = Patient.query.join(Patient.user).all()
    doctors = Staff.query.join(Staff.user).all()
    return render_template("add_appointment_admin.html", patients=patients, doctors=doctors, user=current_user)

@main_bp.route("/update_appointment/<int:appointment_id>", methods=["GET", "POST"])
@login_required
@roles_required("doctor")
def update_appointment(appointment_id):
    staff = current_user.staff
    if not staff:
        return "Error: No staff record found", 404
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # preveri če je app. od tega doktorja
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
    
    patients = Patient.query.join(Patient.user).all()
    return render_template("update_appointment.html", appointment=appointment, patients=patients, user=current_user)

@main_bp.route("/update_appointment_admin/<int:appointment_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_appointment_admin(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if request.method == "POST":
        try:
            appointment.staff_id = int(request.form.get('doctor_id'))
            appointment.patient_id = int(request.form.get('patient_id'))
            appointment.appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
            appointment.appointment_time = datetime.strptime(request.form.get('appointment_time'), '%H:%M').time()
            appointment.status = request.form.get('status', 'pending')
            
            db.session.commit()
            flash("Pregled uspešno posodobljen", "success")
            return redirect(url_for("main.appointment_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju pregleda: {str(e)}", "danger")
    
    # pacienti za dropdown
    patients = Patient.query.join(Patient.user).all()
    doctors = Staff.query.join(Staff.user).all()
    return render_template("update_appointment_admin.html", appointment=appointment, patients=patients, doctors=doctors, user=current_user)

@main_bp.route("/delete_appointment/<int:appointment_id>", methods=["POST"])
@login_required
@roles_required("doctor", "admin")
def delete_appointment(appointment_id):
    staff = current_user.staff
    appointment = Appointment.query.get_or_404(appointment_id)
    redirect_url = _redirect_for_role(staff, "main.appointment_admin", "main.appointment_doctor")
    return _delete_record_and_redirect(
        lambda: _delete_appointment_record(appointment),
        "Pregled uspešno izbrisan",
        "Napaka pri brisanju pregleda",
        redirect_url
    )

# CRUD za Diagnoze
@main_bp.route("/add_diagnosis", methods=["GET", "POST"])
@login_required
@roles_required("doctor", "admin")
def add_diagnosis():
    staff = current_user.staff

    if request.method == "POST":
        try:
            appointment_id = int(request.form.get('appointment_id'))
            description = request.form.get('description', '').strip()
            
            appointment = Appointment.query.get_or_404(appointment_id)
            if staff and appointment.staff_id != staff.staff_id:
                flash("Nimate dostopa do tega pregleda", "danger")
                return redirect(url_for("main.add_diagnosis"))
            
            diagnosis = Diagnosis(
                appointment_id=appointment_id,
                description=description
            )
            db.session.add(diagnosis)
            db.session.commit()
            flash("Diagnoza uspešno dodana", "success")
            if not staff:
                return redirect(url_for("main.diagnosis_admin"))
            return redirect(url_for("main.diagnosis_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju diagnoze: {str(e)}", "danger")
    
    if not staff:
        appointments = Appointment.query.all()
    else:
        appointments = Appointment.query.filter_by(staff_id=staff.staff_id).all()
    return render_template("add_diagnosis.html", appointments=appointments, user=current_user)

@main_bp.route("/update_diagnosis/<int:diagnosis_id>", methods=["GET", "POST"])
@login_required
@roles_required("doctor", "admin")
def update_diagnosis(diagnosis_id):
    staff = current_user.staff

    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    
    appointment = Appointment.query.get_or_404(diagnosis.appointment_id)
    if staff and appointment.staff_id != staff.staff_id:
        flash("Nimate dostopa do te diagnoze", "danger")
        return redirect(url_for("main.diagnosis_doctor"))
    
    if request.method == "POST":
        try:
            diagnosis.description = request.form.get('description', '').strip()
            
            db.session.commit()
            flash("Diagnoza uspešno posodobljena", "success")
            if not staff:
                return redirect(url_for("main.diagnosis_admin"))
            return redirect(url_for("main.diagnosis_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju diagnoze: {str(e)}", "danger")
    
    return render_template("update_diagnosis.html", diagnosis=diagnosis, user=current_user)

@main_bp.route("/delete_diagnosis/<int:diagnosis_id>", methods=["POST"])
@login_required
@roles_required("doctor", "admin")
def delete_diagnosis(diagnosis_id):
    staff = current_user.staff
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)

    appointment = Appointment.query.get_or_404(diagnosis.appointment_id)
    if staff and appointment.staff_id != staff.staff_id:
        flash("Nimate dostopa do te diagnoze", "danger")
        return redirect(url_for("main.diagnosis_doctor"))

    redirect_url = _redirect_for_role(staff, "main.diagnosis_admin", "main.diagnosis_doctor")
    return _delete_record_and_redirect(
        lambda: db.session.delete(diagnosis),
        "Diagnoza uspešno izbrisana",
        "Napaka pri brisanju diagnoze",
        redirect_url
    )

@main_bp.route("/delete_admission/<int:admission_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def delete_admission(admission_id):
    admission = Admission.query.get_or_404(admission_id)
    return _delete_record_and_redirect(
        lambda: db.session.delete(admission),
        "Sprejem uspešno izbrisan",
        "Napaka pri brisanju sprejema",
        url_for("main.admission_admin")
    )

# CRUD za admissone
@main_bp.route("/add_admission", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_admission():
    
    if request.method == "POST":
        try:
            patient_id = int(request.form.get('patient_id'))
            bed_id = int(request.form.get('bed_id'))
            admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d').date()

            admission = Admission(
                patient_id=patient_id,
                bed_id=bed_id,
                admitted_date=admission_date,
                discharged_date=None
            )
            db.session.add(admission)
            db.session.commit()
            flash("Sprejem uspešno dodan", "success")
            return redirect(url_for("main.admission_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju sprejema: {str(e)}", "danger")
    
    
    patients = Patient.query.join(Patient.user).all()
    beds = Bed.query.join(Bed.room).all()
    return render_template("add_admission.html", patients=patients, beds=beds, user=current_user)

@main_bp.route("/update_admission/<int:admission_id>", methods=["GET", "POST"])
@login_required
@roles_required("doctor", "admin")
def update_admission(admission_id):
    staff = current_user.staff
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
            if not staff:
                return redirect(url_for("main.admission_admin"))
            return redirect(url_for("main.admission_doctor"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju sprejema: {str(e)}", "danger")
    
    patients = Patient.query.join(Patient.user).all()
    beds = Bed.query.all()
    return render_template("update_admission.html", admission=admission, patients=patients, beds=beds, user=current_user)

# Pacient routi
@main_bp.route("/appointment_patient")
@login_required
@roles_required("patient")
def appointment_patient():
    patient = current_user.patient
    patient_id = patient.patient_id if patient else -1
    
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    query = Appointment.query.filter_by(patient_id=patient_id)
    
    if search:
        try:
            staff_id = int(search)
            query = query.filter_by(staff_id=staff_id)
        except ValueError:
            # Search by staff name (via Staff -> User relationship)
            from app.models.user import User
            query = query.join(Staff).join(User).filter(User.name.ilike(f'%{search}%'))
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    data_rows = []
    for apt in appointments:
        try: 
            tname = apt.staff_member.name()
        except:
            continue

        data_rows.append({
            'appointment_id': apt.appointment_id,
            'staff_name': tname,
            'appointment_date': apt.appointment_date,
            'appointment_time': apt.appointment_time,
            'status': apt.status or 'pending'
        })
    
    return render_template("appointment_patient.html", data_rows=data_rows, user=current_user)

@main_bp.route("/diagnosis_patient")
@login_required
@roles_required("patient")
def diagnosis_patient():
    patient = current_user.patient
    patient_id = patient.patient_id if patient else -1
    
    search = request.args.get('search', '').strip()
    
    query = Diagnosis.query.join(Appointment).filter(Appointment.patient_id == patient_id)
    
    if search:
        query = query.filter(Diagnosis.description.ilike(f'%{search}%'))
    
    diagnoses = query.order_by(Diagnosis.diagnosis_id.desc()).all()

    diagnosis_rows = []
    for diag in diagnoses:
        diagnosis_rows.append({
            'diagnosis_id': diag.diagnosis_id,
            'appointment_id': diag.appointment_id,
            'description': diag.description
        })
    
    return render_template("diagnosis_patient.html", diagnosis_rows=diagnosis_rows, user=current_user)

@main_bp.route("/admission_patient")
@login_required
@roles_required("patient")
def admission_patient():
    patient = current_user.patient
    patient_id = patient.patient_id if patient else -1
    
    search = request.args.get('search', '').strip()
    
    query = Admission.query.filter_by(patient_id=patient_id)
    
    if search:
        try:
            bed_id = int(search)
            query = query.filter_by(bed_id=bed_id)
        except ValueError:
            pass 
    
    admissions = query.order_by(Admission.admitted_date.desc()).all()
    
    admission_rows = []
    for adm in admissions:
        bed = Bed.query.get(adm.bed_id)
        bed_info = f'Postelja {adm.bed_id}'
        if bed:
            bed_info = f'Postelja {adm.bed_id} (Soba {bed.room_id})'
        
        admission_rows.append({
            'admission_id': adm.admission_id,
            'bed_id': adm.bed_id,
            'bed_info': bed_info,
            'admitted_date': adm.admitted_date,
            'discharged_date': adm.discharged_date
        })
    
    return render_template("admission_patient.html", admission_rows=admission_rows, user=current_user)

# routi za admina

# Admin Dashboard
@main_bp.route("/user_admin")
@login_required
@roles_required("admin")
def user_admin():
    search = request.args.get('search', '').strip()
    query = User.query

    if search:
        try:
            user_id = int(search)
            query = query.filter(User.user_id == user_id)
        except ValueError:
            query = query.filter(
                (User.name.ilike(f'%{search}%')) |
                (User.username.ilike(f'%{search}%'))
            )
    
    users = query.order_by(User.user_id).all()
    user_rows = []
    for user in users:
        user_rows.append({
            'user_id': user.user_id,
            'name': user.name,
            'username': user.username,
            'phone': user.phone or '',
            'role': user.role.value
        })
    return render_template("user_admin.html", user_rows=user_rows, user=current_user, search=search)

# Add User
@main_bp.route("/add_user", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_user():
    if request.method == "POST":
        try:
            name = request.form.get('name', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            phone = request.form.get('phone', '').strip()
            role_str = request.form.get('role', '').strip()
            
            if not name or not username or not password or not role_str:
                flash("Vsa obvezna polja morajo biti izpolnjena", "danger")
                return render_template("add_user.html", user=current_user)
            
            if User.query.filter_by(username=username).first():
                flash("Uporabniško ime že obstaja", "danger")
                return render_template("add_user.html", user=current_user)
            
            role = RoleEnum[role_str.upper()]
            password_hash = generate_password_hash(password)
            
            new_user = User(
                name=name,
                username=username,
                password_hash=password_hash,
                phone=phone if phone else None,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            if role == RoleEnum.PATIENT:
                patient = Patient(user_id=new_user.user_id, gender=None, address=None)
                db.session.add(patient)
                db.session.commit()
            elif role == RoleEnum.DOCTOR:
                dept = Department.query.first()
                staff = Staff(user_id=new_user.user_id, role="doctor", department_id=dept.department_id if dept else None)
                db.session.add(staff)
                db.session.commit()
            
            flash("Uporabnik uspešno dodan", "success")
            return redirect(url_for("main.user_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju uporabnika: {str(e)}", "danger")
    
    return render_template("add_user.html", user=current_user)

@main_bp.route("/add_patient", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_patient():
    if request.method == "POST":
        try:
            name = request.form.get('name', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            phone = request.form.get('phone', '').strip()
            
            if not name or not username or not password:
                flash("Vsa obvezna polja morajo biti izpolnjena", "danger")
                return render_template("add_patient.html", user=current_user)
            
            if User.query.filter_by(username=username).first():
                flash("Uporabniško ime že obstaja", "danger")
                return render_template("add_patient.html", user=current_user)
            
            role = RoleEnum["PATIENT"]
            password_hash = generate_password_hash(password)
            
            new_user = User(
                name=name,
                username=username,
                password_hash=password_hash,
                phone=phone if phone else None,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            patient = Patient(user_id=new_user.user_id, gender=None, address=None)
            db.session.add(patient)
            db.session.commit()
            
            flash("Pacient uspešno dodan", "success")
            return redirect(url_for("main.user_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju uporabnika: {str(e)}", "danger")
    
    return render_template("add_patient.html", user=current_user)

# Update User
@main_bp.route("/update_user/<int:user_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == "POST":
        try:
            user.name = request.form.get('name', '').strip()
            user.username = request.form.get('username', '').strip()
            phone = request.form.get('phone', '').strip()
            role_str = request.form.get('role', '').strip()
            
            existing_user = User.query.filter_by(username=user.username).first()
            if existing_user and existing_user.user_id != user_id:
                flash("Uporabniško ime že obstaja", "danger")
                return render_template("update_user.html", user_obj=user, current_user=current_user)
            
            user.phone = phone if phone else None
            user.role = RoleEnum[role_str.upper()]
            
            new_password = request.form.get('password', '').strip()
            if new_password:
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            flash("Uporabnik uspešno posodobljen", "success")
            return redirect(url_for("main.user_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju uporabnika: {str(e)}", "danger")
    
    return render_template("update_user.html", user_obj=user, current_user=current_user)

# Delete User
@main_bp.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    return _delete_record_and_redirect(
        lambda: _delete_user_record(user),
        "Uporabnik uspešno izbrisan",
        "Napaka pri brisanju uporabnika",
        url_for("main.user_admin")
    )

# View all patients
@main_bp.route("/patient_admin")
@login_required
@roles_required("admin")
def patient_admin():
    search = request.args.get('search', '').strip()
    
    query = Patient.query
    
    if search:
        try:
            patient_id = int(search)
            query = query.filter(Patient.patient_id == patient_id)
        except ValueError:
            from app.models.user import User
            query = query.join(User).filter(User.name.ilike(f'%{search}%'))
    
    patients = query.order_by(Patient.patient_id).all()
    patient_rows = []
    for patient in patients:
        patient_rows.append({
            'patient_id': patient.patient_id,
            'name': patient.user.name if patient.user else 'N/A',
            'username': patient.user.username if patient.user else 'N/A',
            'gender': patient.gender or '',
            'address': patient.address or ''
        })
    return render_template("patient_admin.html", patient_rows=patient_rows, user=current_user, search=search)

# poglej ves staff
@main_bp.route("/staff_admin")
@login_required
@roles_required("admin")
def staff_admin():
    search = request.args.get('search', '').strip()
    
    query = Staff.query
    
    if search:
        try:
            staff_id = int(search)
            query = query.filter(Staff.staff_id == staff_id)
        except ValueError:
            from app.models.user import User
            from sqlalchemy import or_
            query = query.join(User, Staff.user_id == User.user_id).outerjoin(
                Department, Staff.department_id == Department.department_id
            ).filter(
                or_(
                    User.name.ilike(f'%{search}%'),
                    Department.name.ilike(f'%{search}%')
                )
            )
    
    staff_members = query.order_by(Staff.staff_id).all()
    staff_rows = []
    for staff in staff_members:
        dept_name = staff.department.name if staff.department else 'N/A'
        staff_rows.append({
            'staff_id': staff.staff_id,
            'name': staff.user.name if staff.user else 'N/A',
            'username': staff.user.username if staff.user else 'N/A',
            'role': staff.role or '',
            'department': dept_name
        })
    return render_template("staff_admin.html", staff_rows=staff_rows, user=current_user, search=search)

# View all appointments
@main_bp.route("/appointment_admin")
@login_required
@roles_required("admin")
def appointment_admin():
    search = request.args.get('search', '').strip()
    
    query = Appointment.query
    
    if search:
        try:
            appointment_id = int(search)
            query = query.filter(Appointment.appointment_id == appointment_id)
        except ValueError:
            # Search by patient name or doctor name
            from app.models.user import User
            from sqlalchemy import or_, alias
            # Create aliases for User table to join twice
            patient_user = alias(User)
            doctor_user = alias(User)
            query = query.join(Patient, Appointment.patient_id == Patient.patient_id).join(
                patient_user, Patient.user_id == patient_user.c.user_id
            ).join(Staff, Appointment.staff_id == Staff.staff_id).join(
                doctor_user, Staff.user_id == doctor_user.c.user_id
            ).filter(
                or_(
                    patient_user.c.name.ilike(f'%{search}%'),
                    doctor_user.c.name.ilike(f'%{search}%')
                )
            )
    
    appointments = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    appointment_rows = []
    for apt in appointments:
        patient_name = 'N/A'
        doctor_name = 'N/A'
        if apt.patient and apt.patient.user:
            patient_name = apt.patient.user.name
        if apt.staff_member and apt.staff_member.user:
            doctor_name = apt.staff_member.user.name
        
        appointment_rows.append({
            'appointment_id': apt.appointment_id,
            'patient_id': apt.patient_id,
            'patient_name': patient_name,
            'staff_id': apt.staff_id,
            'doctor_name': doctor_name,
            'appointment_date': apt.appointment_date,
            'appointment_time': apt.appointment_time,
            'status': apt.status or 'pending'
        })
    return render_template("appointment_admin.html", appointment_rows=appointment_rows, user=current_user, search=search)

# View all admissions
@main_bp.route("/admission_admin")
@login_required
@roles_required("admin")
def admission_admin():
    search = request.args.get('search', '').strip()
    query = Admission.query
    
    if search:
        try:
            search_id = int(search)
            query = query.filter(
                (Admission.admission_id == search_id) |
                (Admission.patient_id == search_id) |
                (Admission.bed_id == search_id)
            )
        except ValueError:
            from app.models.user import User
            query = query.join(Patient).join(User).filter(User.name.ilike(f'%{search}%'))
    
    admissions = query.order_by(Admission.admitted_date.desc()).all()
    admission_rows = []
    for adm in admissions:
        patient_name = 'N/A'
        if adm.patient and adm.patient.user:
            patient_name = adm.patient.user.name
        
        bed_info = f'Postelja {adm.bed_id}'
        if adm.bed:
            bed_info = f'Postelja {adm.bed_id} (Soba {adm.bed.room_id})'
        
        admission_rows.append({
            'admission_id': adm.admission_id,
            'patient_id': adm.patient_id,
            'patient_name': patient_name,
            'bed_id': adm.bed_id,
            'bed_info': bed_info,
            'admitted_date': adm.admitted_date,
            'discharged_date': adm.discharged_date
        })
    return render_template("admission_admin.html", admission_rows=admission_rows, user=current_user, search=search)

# View all diagnoses
@main_bp.route("/diagnosis_admin")
@login_required
@roles_required("admin")
def diagnosis_admin():
    search = request.args.get('search', '').strip()
    
    query = Diagnosis.query
    
    if search:
        try:
            search_id = int(search)
            query = query.filter(
                (Diagnosis.diagnosis_id == search_id) |
                (Diagnosis.appointment_id == search_id)
            )
        except ValueError:
            query = query.filter(Diagnosis.description.ilike(f'%{search}%'))
    
    diagnoses = query.order_by(Diagnosis.diagnosis_id.desc()).all()
    diagnosis_rows = []
    for diag in diagnoses:
        diagnosis_rows.append({
            'diagnosis_id': diag.diagnosis_id,
            'appointment_id': diag.appointment_id,
            'description': diag.description
        })
    return render_template("diagnosis_admin.html", diagnosis_rows=diagnosis_rows, user=current_user, search=search)

# View all departments
@main_bp.route("/department_admin")
@login_required
@roles_required("admin")
def department_admin():
    search = request.args.get('search', '').strip()
    
    query = Department.query
    
    if search:
        try:
            dept_id = int(search)
            query = query.filter(Department.department_id == dept_id)
        except ValueError:
            query = query.filter(
                (Department.name.ilike(f'%{search}%')) |
                (Department.location.ilike(f'%{search}%'))
            )
    
    departments = query.order_by(Department.department_id).all()
    department_rows = []
    for dept in departments:
        department_rows.append({
            'department_id': dept.department_id,
            'name': dept.name,
            'location': dept.location or ''
        })
    return render_template("department_admin.html", department_rows=department_rows, user=current_user, search=search)

# View all rooms
@main_bp.route("/room_admin")
@login_required
@roles_required("admin")
def room_admin():
    search = request.args.get('search', '').strip()
    
    query = Room.query
    
    # Apply search filter
    if search:
        try:
            # Try to search by room ID or department ID
            search_id = int(search)
            query = query.filter(
                (Room.room_id == search_id) |
                (Room.department_id == search_id)
            )
        except ValueError:
            # Search by type or department name
            query = query.join(Department).filter(
                (Room.type.ilike(f'%{search}%')) |
                (Department.name.ilike(f'%{search}%'))
            )
    
    rooms = query.order_by(Room.room_id).all()
    room_rows = []
    for room in rooms:
        dept_name = room.department.name if room.department else 'N/A'
        room_rows.append({
            'room_id': room.room_id,
            'type': room.type or '',
            'department_id': room.department_id,
            'department_name': dept_name
        })
    return render_template("room_admin.html", room_rows=room_rows, user=current_user, search=search)


#Dodaj sobo
@main_bp.route("/add_room", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_room():
    
    if request.method == "POST":
        try:
            room_type = request.form.get('room_type')
            department_id = int(request.form.get('department_id'))

            room = Room(
                type=room_type,
                department_id=department_id,
            )

            db.session.add(room)
            db.session.commit()
            flash("Soba uspešno dodana", "success")
            return redirect(url_for("main.room_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju sobe: {str(e)}", "danger")
    
    
    departments = Department.query.all()
    return render_template("add_room.html", departments=departments, user=current_user)

#updataj sobo
@main_bp.route("/update_room/<int:room_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_room(room_id):

    
    room = Room.query.get_or_404(room_id)
    
    if request.method == "POST":
        try:
            room.type = request.form.get('room_type')
            room.department_id = request.form.get('department_id')
            
            db.session.commit()
            flash("Soba uspešno posodobljena", "success")
            return redirect(url_for("main.room_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju sobe: {str(e)}", "danger")
    
    departments = Department.query.all()
    return render_template("update_room.html", room=room, departments=departments, user=current_user)

#zbriši sobo
@main_bp.route("/delete_room/<int:room_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    return _delete_record_and_redirect(
        lambda: _delete_room_record(room),
        "Soba uspešno izbrisana",
        "Napaka pri brisanju sobe",
        url_for("main.room_admin")
    )


# View all beds
@main_bp.route("/bed_admin")
@login_required
@roles_required("admin")
def bed_admin():
    search = request.args.get('search', '').strip()
    
    query = Bed.query
    
    # Apply search filter
    if search:
        try:
            # Try to search by bed ID or room ID
            search_id = int(search)
            query = query.filter(
                (Bed.bed_id == search_id) |
                (Bed.room_id == search_id)
            )
        except ValueError:
            # Search by status
            query = query.filter(Bed.status.ilike(f'%{search}%'))
    
    beds = query.order_by(Bed.bed_id).all()
    bed_rows = []
    for bed in beds:
        bed_rows.append({
            'bed_id': bed.bed_id,
            'room_id': bed.room_id,
            'status': bed.status or ''
        })
    return render_template("bed_admin.html", bed_rows=bed_rows, user=current_user, search=search)

#dodaj posteljo
@main_bp.route("/add_bed", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def add_bed():
    
    if request.method == "POST":
        try:
            room_id = request.form.get('room_id')
            status = request.form.get('bed_status')

            bed = Bed(
                room_id=room_id,
                status=status,
            )

            db.session.add(bed)
            db.session.commit()
            flash("Postleja uspešno dodana", "success")
            return redirect(url_for("main.bed_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri dodajanju postelje: {str(e)}", "danger")
    
    rooms = Room.query.join(Department).all()
    return render_template("add_bed.html", rooms=rooms, user=current_user)


#udpataj posteljo
@main_bp.route("/update_bed/<int:bed_id>", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def update_bed(bed_id):

    
    bed = Bed.query.get_or_404(bed_id)
    
    if request.method == "POST":
        try:
            bed.room_id = request.form.get('room_id')
            bed.status = request.form.get('bed_status')
            
            db.session.commit()
            flash("Postelja uspešno posodobljena", "success")
            return redirect(url_for("main.bed_admin"))
        except Exception as e:
            db.session.rollback()
            flash(f"Napaka pri posodabljanju postelje: {str(e)}", "danger")
    
    rooms = Room.query.join(Department).all()
    return render_template("update_bed.html", bed=bed, rooms=rooms, user=current_user)

#izbriši posteljo
@main_bp.route("/delete_bed/<int:bed_id>", methods=["POST"])
@login_required
@roles_required("admin")
def delete_bed(bed_id):
    bed = Bed.query.get_or_404(bed_id)
    return _delete_record_and_redirect(
        lambda: _delete_bed_record(bed),
        "Postelja uspešno izbrisana",
        "Napaka pri brisanju postelje",
        url_for("main.bed_admin")
    )

