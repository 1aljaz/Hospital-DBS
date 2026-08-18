from app import create_app
from app.db import db
from app.factories import (
    create_admin,
    create_doctor,
    create_patient,
    create_departments_and_staff,
    create_patients,
    create_rooms_and_beds,
    create_appointments,
    create_admissions,
    create_diagnoses
)
from app.models.staff import Staff
from app.models.patient import Patient

app = create_app()

with app.app_context():
    print("Creating admin user...")
    admin = create_admin()
    print("Creating doctor user...")
    doctor = create_doctor()
    print("Creating patient user...")
    patient = create_patient()
    
    print("Creating departments and staff...")
    departments, staff_members = create_departments_and_staff(num_departments=3, num_doctors_per_dept=3)
    staff_members.append(Staff.query.filter_by(user_id=doctor.user_id).first())

    print("Creating patients...")
    patients = create_patients(num_patients=20)
    patients.append(Patient.query.filter_by(user_id=patient.user_id).first())

    print("Creating rooms and beds...")
    rooms, beds = create_rooms_and_beds(departments)

    print("Creating appointments...")
    appointments = create_appointments(patients, staff_members, num_appointments=50)

    print("Creating admissions...")
    admissions = create_admissions(patients, beds, num_admissions=30)

    print("Creating diagnoses for appointments...")
    diagnoses = create_diagnoses(appointments)

    print("Database fully seeded.")
