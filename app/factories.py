from app.db import db
from app.models.user import User, RoleEnum
from app.models.patient import Patient
from app.models.staff import Staff
from app.models.department import Department
from app.models.room import Room
from app.models.bed import Bed
from app.models.appointment import Appointment
from app.models.admission import Admission
from werkzeug.security import generate_password_hash
import random
from datetime import date, datetime, timedelta
import faker

fake = faker.Faker()

# --- Helpers ---
def random_phone():
    return f"+1-{random.randint(100,999)}-{random.randint(1000,9999)}"

def random_gender():
    return random.choice(["Male", "Female", "Other"])


def create_departments_and_staff(num_departments=3, num_doctors_per_dept=3):
    departments = []
    staff_members = []

    for _ in range(num_departments):
        dept = Department(
            name=fake.word().capitalize() + " Dept",
            location=f"{random.randint(1,5)}th Floor"
        )
        db.session.add(dept)
        db.session.commit()
        departments.append(dept)

        for _ in range(num_doctors_per_dept):
            user = User(
                name=fake.name(),
                username=fake.unique.user_name(),
                password_hash=generate_password_hash("doctorpass"),
                role=RoleEnum.DOCTOR,
                phone=random_phone()
            )
            db.session.add(user)
            db.session.commit()

            staff = Staff(user_id=user.user_id, role="doctor", department_id=dept.department_id)
            db.session.add(staff)
            db.session.commit()
            staff_members.append(staff)

    return departments, staff_members

def create_patients(num_patients=20):
    patients = []
    for _ in range(num_patients):
        user = User(
            name=fake.name(),
            username=fake.unique.user_name(),
            password_hash=generate_password_hash("patientpass"),
            role=RoleEnum.PATIENT,
            phone=random_phone()
        )
        db.session.add(user)
        db.session.commit()

        patient = Patient(
            user_id=user.user_id,
            gender=random_gender(),
            address=fake.address()
        )
        db.session.add(patient)
        db.session.commit()
        patients.append(patient)
    return patients


def create_rooms_and_beds(departments, beds_per_room=2):
    rooms = []
    beds = []

    for dept in departments:
        for _ in range(2):  # 2 rooms per department
            room = Room(type=random.choice(["ICU", "General"]), department_id=dept.department_id)
            db.session.add(room)
            db.session.commit()
            rooms.append(room)

            for _ in range(beds_per_room):
                bed = Bed(room_id=room.room_id, status=random.choice(["free", "occupied"]))
                db.session.add(bed)
                db.session.commit()
                beds.append(bed)
    return rooms, beds


def create_appointments(patients, staff_members, num_appointments=50):
    appointments = []
    for _ in range(num_appointments):
        patient = random.choice(patients)
        staff = random.choice(staff_members)
        appt_date = date.today() + timedelta(days=random.randint(0, 30))
        appt_time = datetime.now().time()
        status = random.choice(["scheduled", "completed", "canceled"])

        appt = Appointment(
            patient_id=patient.patient_id,
            staff_id=staff.staff_id,
            appointment_date=appt_date,
            appointment_time=appt_time,
            status=status
        )
        db.session.add(appt)
        db.session.commit()
        appointments.append(appt)
    return appointments


def create_admissions(patients, beds, num_admissions=30):
    admissions = []
    for _ in range(num_admissions):
        patient = random.choice(patients)
        bed = random.choice(beds)
        admitted_date = date.today() - timedelta(days=random.randint(0, 10))
        discharged_date = admitted_date + timedelta(days=random.randint(1, 5)) if random.random() < 0.5 else None

        admission = Admission(
            patient_id=patient.patient_id,
            bed_id=bed.bed_id,
            admitted_date=admitted_date,
            discharged_date=discharged_date
        )
        db.session.add(admission)
        db.session.commit()
        admissions.append(admission)
    return admissions


from app.models.diagnosis import Diagnosis

def create_diagnoses(appointments, num_diagnoses=None):
    """
    Create diagnoses linked to appointments.
    If num_diagnoses is None, create one diagnosis per appointment randomly.
    """
    diagnoses = []
    for appt in appointments:
        if num_diagnoses is None:
            if random.random() < 0.7: 
                description = random.choice([
                    "Flu",
                    "Fracture",
                    "High blood pressure",
                    "Diabetes checkup",
                    "Routine physical",
                    "Migraine",
                    "Allergy reaction",
                    "Heart condition"
                ])
                diag = Diagnosis(
                    appointment_id=appt.appointment_id,
                    description=description
                )
                db.session.add(diag)
                db.session.commit()
                diagnoses.append(diag)
        else:
            # Create fixed number of diagnoses
            for _ in range(num_diagnoses):
                description = random.choice([
                    "Flu",
                    "Fracture",
                    "High blood pressure",
                    "Diabetes checkup",
                    "Routine physical",
                    "Migraine",
                    "Allergy reaction",
                    "Heart condition"
                ])
                diag = Diagnosis(
                    appointment_id=appt.appointment_id,
                    description=description
                )
                db.session.add(diag)
                db.session.commit()
                diagnoses.append(diag)
    return diagnoses

