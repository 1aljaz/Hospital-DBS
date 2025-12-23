from app import create_app
from app.db import db
from app.factories import (
    create_departments_and_staff,
    create_patients,
    create_rooms_and_beds,
    create_appointments,
    create_admissions,
    create_diagnoses
)

app = create_app()

with app.app_context():
    print("Creating departments and staff...")
    departments, staff_members = create_departments_and_staff(num_departments=3, num_doctors_per_dept=3)

    print("Creating patients...")
    patients = create_patients(num_patients=20)

    print("Creating rooms and beds...")
    rooms, beds = create_rooms_and_beds(departments)

    print("Creating appointments...")
    appointments = create_appointments(patients, staff_members, num_appointments=50)

    print("Creating admissions...")
    admissions = create_admissions(patients, beds, num_admissions=30)

    print("Creating diagnoses for appointments...")
    diagnoses = create_diagnoses(appointments)

    print("Database fully seeded with realistic data!")
