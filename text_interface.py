import re
from datetime import datetime
# Import your Flask app instance (adjust this to your factory function if necessary)
from run import app 

def clean_html(raw_html):
    """Strips HTML tags and removes excessive blank lines to clean up CLI outputs."""
    text = raw_html.decode('utf-8')
    clean_text = re.sub('<.*?>', ' ', text)
    return "\n".join([line.strip() for line in clean_text.splitlines() if line.strip()])

# ==========================================
# ADMIN SUB-MENUS (CRUD for 2 Categories)
# ==========================================
def admin_department_crud(client):
    while True:
        print("\n--- [Admin] Department CRUD ---")
        print("1. Create Department")
        print("2. Read / View Departments Dashboard")
        print("3. Update Department")
        print("4. Delete Department")
        print("0. Back to Admin Menu")
        choice = input("Select operation: ")

        if choice == '1':
            name = input("Enter Department Name: ").strip()
            location = input("Enter Department Location: ").strip()
            res = client.post('/add_department', data={'name': name, 'location': location}, follow_redirects=True)
            print("\n[Server Response]:")
            print(clean_html(res.data)[:300] + "...")
        elif choice == '2':
            res = client.get('/department_admin')
            print("\n" + clean_html(res.data))
        elif choice == '3':
            dept_id = input("Enter Department ID to update: ").strip()
            name = input("Enter New Department Name: ").strip()
            location = input("Enter New Department Location: ").strip()
            res = client.post(f'/update_department/{dept_id}', data={
                'department_name': name,
                'department_location': location
            }, follow_redirects=True)
            print("\n[Server Response]: Update requested.")
        elif choice == '4':
            dept_id = input("Enter Department ID to delete: ").strip()
            res = client.post(f'/delete_department/{dept_id}', follow_redirects=True)
            print("\n[Server Response]: Deletion requested.")
        elif choice == '0':
            break

def admin_staff_crud(client):
    while True:
        print("\n--- [Admin] Staff CRUD ---")
        print("1. Create Staff Member")
        print("2. Read / View Staff Dashboard")
        print("3. Update Staff Member")
        print("4. Delete Staff Member")
        print("0. Back to Admin Menu")
        choice = input("Select operation: ")

        if choice == '1':
            name = input("Full Name: ").strip()
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            role = input("Role (doctor/admin/patient): ").strip()
            res = client.post('/add_staff', data={
                'name': name,
                'username': username,
                'password': password,
                'role': role
            }, follow_redirects=True)
            print("\n[Server Response]:")
            print(clean_html(res.data)[:300] + "...")
        elif choice == '2':
            res = client.get('/staff_admin')
            print("\n" + clean_html(res.data))
        elif choice == '3':
            staff_id = input("Enter Staff ID to update: ").strip()
            name = input("Enter New Full Name: ").strip()
            role = input("Enter New Role (doctor/admin): ").strip()
            dept_id = input("Enter Department ID: ").strip()
            res = client.post(f'/update_staff/{staff_id}', data={
                'name': name,
                'role': role,
                'department_id': dept_id
            }, follow_redirects=True)
            print("\n[Server Response]: Update requested.")
        elif choice == '4':
            staff_id = input("Enter Staff ID to delete: ").strip()
            res = client.post(f'/delete_staff/{staff_id}', follow_redirects=True)
            print("\n[Server Response]: Deletion requested.")
        elif choice == '0':
            break

# ==========================================
# ROLE MAIN MENUS
# ==========================================
def admin_menu(client):
    while True:
        print("\n=== ADMIN DASHBOARD ===")
        print("1. Manage Departments (Category 1 CRUD)")
        print("2. Manage Staff (Category 2 CRUD)")
        print("0. Logout & Exit")
        choice = input("Select an option: ")
        if choice == '1':
            admin_department_crud(client)
        elif choice == '2':
            admin_staff_crud(client)
        elif choice == '0':
            break

def doctor_menu(client):
    while True:
        print("\n=== DOCTOR DASHBOARD ===")
        print("1. View My Scheduled Appointments (Read)")
        print("2. Update an Appointment (Update)")
        print("0. Logout & Exit")
        choice = input("Select an option: ")
        
        if choice == '1':
            res = client.get('/appointment_doctor')
            print("\n" + clean_html(res.data))
        elif choice == '2':
            apt_id = input("Enter Appointment ID to update: ").strip()
            p_id = input("Patient ID: ").strip()
            date = input("Appointment Date (YYYY-MM-DD): ").strip()
            time = input("Appointment Time (HH:MM): ").strip()
            status = input("Status (pending/completed/cancelled): ").strip()
            
            res = client.post(f'/update_appointment/{apt_id}', data={
                'patient_id': p_id,
                'appointment_date': date,
                'appointment_time': time,
                'status': status
            }, follow_redirects=True)
            print("\n[Server Response]: Appointment updated.")
        elif choice == '0':
            break

def patient_menu(client):
    while True:
        print("\n=== PATIENT DASHBOARD ===")
        print("1. View My Appointments (Read)")
        print("0. Logout & Exit")
        choice = input("Select an option: ")
        
        if choice == '1':
            res = client.get('/appointment_patient')
            print("\n" + clean_html(res.data))
        elif choice == '0':
            break

# ==========================================
# MAIN EXECUTION & AUTOMATIC ROLE CHECK
# ==========================================
def run_terminal_interface():
    # Context-managed browser session
    with app.test_client() as client:
        print("=== Hospital Database System CLI ===")
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        # Hits your auth route directly
        login_response = client.post('/auth/', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

        # Catch authentication validation errors matching auth.py flash messages
        if b"Invalid username" in login_response.data:
            print("\n[ERROR] Login failed: Invalid username or password.")
            return

        # AUTOMATIC ROLE DETECTION FROM REDIRECT DESTINATION
        final_path = login_response.request.path
        print(f"\n[SUCCESS] Authentication verified. Server routed context to: {final_path}")

        if "/admin" in final_path:
            admin_menu(client)
        elif "/doctor" in final_path:
            doctor_menu(client)
        elif "/patient" in final_path:
            patient_menu(client)
        else:
            print("[System Notice] Logged into index view or role context could not be parsed.")
            
        client.get('/auth/logout')
        print("Session destroyed safely. Goodbye!")

if __name__ == '__main__':
    run_terminal_interface()