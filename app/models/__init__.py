# app/models/__init__.py

from .user import User
from .patient import Patient
from .staff import Staff
from .department import Department
from .room import Room
from .bed import Bed
from .appointment import Appointment
from .admission import Admission
from .diagnosis import Diagnosis

# Optional: expose all models as a list (useful for migrations)
all_models = [
    User,
    Patient,
    Staff,
    Department,
    Room,
    Bed,
    Appointment,
    Admission,
    Diagnosis
]
