import re
from datetime import datetime

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
        print("1. Ustvari oddelek")
        print("2. Poglej oddelek")
        print("3. Updataj oddelek")
        print("4. Izbriši oddelek")
        print("0. Nazaj na admin meni")
        choice = input("Izberi: ")

        if choice == '1':
            name = input("Vnesi ime oddelka: ").strip()
            location = input("Vnesi lokacijo oddelka: ").strip()
            res = client.post('/add_department', data={'name': name, 'location': location}, follow_redirects=True)
            print("\n[Server Response]:")
            print(clean_html(res.data)[:300] + "...")
        elif choice == '2':
            res = client.get('/department_admin')
            print("\n" + clean_html(res.data))
        elif choice == '3':
            dept_id = input("Izberi ID oddelka za pospodobitev: ").strip()
            name = input("Vnesi novo ime oddelka: ").strip()
            location = input("Vnesi novo lokacijo oddelka: ").strip()
            res = client.post(f'/update_department/{dept_id}', data={
                'department_name': name,
                'department_location': location
            }, follow_redirects=True)
            print("\n[Server Response]: Update requested.")
        elif choice == '4':
            dept_id = input("Vnesi ID oddelka za izbris: ").strip()
            res = client.post(f'/delete_department/{dept_id}', follow_redirects=True)
            print("\n[Server Response]: Deletion requested.")
        elif choice == '0':
            break

def admin_staff_crud(client):
    while True:
        print("\n--- [Admin] Staff CRUD ---")
        print("1. Dodaj zaposlenega")
        print("2. Preglej zaposlene")
        print("3. Pospodobi zaposlene")
        print("4. Izbriši zaposlene")
        print("0. Nazaj k meniuju za admina")
        choice = input("Izberi: ")

        if choice == '1':
            name = input("Ime in priimek: ").strip()
            username = input("Uporabniško ime: ").strip()
            password = input("Geslo: ").strip()
            role = input("Vloga (doctor/admin/patient): ").strip()
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
            staff_id = input("Vnesi ID zaposlenega za update: ").strip()
            name = input("Vnesi polno ime zaposlenega: ").strip()
            role = input("Vnesi novo vlogo (doctor/admin): ").strip()
            dept_id = input("Vnesi ID oddelka: ").strip()
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
        print("1. Uredi oddelke")
        print("2. Uredi zaposlene")
        print("0. Logout & Exit")
        choice = input("Izberi: ")
        if choice == '1':
            admin_department_crud(client)
        elif choice == '2':
            admin_staff_crud(client)
        elif choice == '0':
            break

def doctor_menu(client):
    while True:
        print("\n=== DOCTOR DASHBOARD ===")
        print("1. Oglej si napovedane preglede")
        print("2. Popravi pregled")
        print("3. Dodaj pregled")
        print("0. Logout & Exit")
        choice = input("Izberi: ")
        
        if choice == '1':
            res = client.get('/appointment_doctor')
            print("\n" + clean_html(res.data))
        elif choice == '2':
            apt_id = input("Vnesi ID pregleda za pospodobitev: ").strip()
            p_id = input("Pacientov ID: ").strip()
            date = input("Datum pregleda (YYYY-MM-DD): ").strip()
            time = input("Čas pregleda (HH:MM): ").strip()
            status = input("Status (pending/completed/cancelled): ").strip()
            
            res = client.post(f'/update_appointment/{apt_id}', data={
                'patient_id': p_id,
                'appointment_date': date,
                'appointment_time': time,
                'status': status
            }, follow_redirects=True)
            print("\n[Server Response]: Appointment updated.")
        elif choice == '3':
            p_id = input("Pacientov ID: ").strip()
            date = input("Datum pregleda (YYYY-MM-DD): ").strip()
            time = input("Čas pregleda (HH:MM): ").strip()
            status = input("Status (pending/completed/cancelled): ").strip()
            
            res = client.post(f'/add_appointment', data={
                'patient_id': p_id,
                'appointment_date': date,
                'appointment_time': time,
                'status': status
            }, follow_redirects=True)
            print("\n[Server Response]: Appointment added.")
            print(clean_html(res.data)[:300] + "...")
        elif choice == '0':
            break

def patient_menu(client):
    while True:
        print("\n=== PATIENT DASHBOARD ===")
        print("1. Poglej svoje preglede")
        print("0. Logout & Exit")
        choice = input("Izberi: ")
        
        if choice == '1':
            res = client.get('/appointment_patient')
            print("\n" + clean_html(res.data))
        elif choice == '0':
            break

# ==========================================
# MAIN EXECUTION 
# ==========================================
def run_terminal_interface():
    # Context-managed browser session
    with app.test_client() as client:
        print("=== Hospital Database System CLI ===")
        username = input("Uporabniško ime: ").strip()
        password = input("Geslo: ").strip()

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