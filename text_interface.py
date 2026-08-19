from datetime import datetime
from getpass import getpass
from html.parser import HTMLParser

from run import app


class _CliTextParser(HTMLParser):
    """Extract readable page content while ignoring navigation and forms."""

    def __init__(self):
        super().__init__()
        self.lines = []
        self.skip_depth = 0
        self.skip_tags = {"nav", "form", "a", "script", "style", "select"}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip_depth += 1
        if tag in {"h1", "h2", "h3", "tr", "p", "li"} and self.skip_depth == 0:
            self.lines.append("\n")

    def handle_endtag(self, tag):
        if tag in {"h1", "h2", "h3", "tr", "p", "li"} and self.skip_depth == 0:
            self.lines.append("\n")
        if tag in self.skip_tags and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth == 0 and data.strip():
            self.lines.append(" ".join(data.split()))


def clean_html(raw_html):
    """Pretvori telo HTTP-odgovora v berljivo besedilo za terminal."""
    parser = _CliTextParser()
    parser.feed(raw_html.decode("utf-8", errors="replace"))
    text = " ".join(parser.lines)
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _print_header(title):
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def _prompt_text(label, required=True):
    while True:
        value = input(f"{label}: ").strip()
        if value or not required:
            return value
        print("[Napaka] Vnos ne sme biti prazen.")


def _prompt_int(label):
    while True:
        value = _prompt_text(label)
        try:
            return int(value)
        except ValueError:
            print("[Napaka] Vnesi celo število.")


def _prompt_date(label):
    while True:
        value = _prompt_text(f"{label} (YYYY-MM-DD)")
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("[Napaka] Uporabi obliko YYYY-MM-DD.")


def _prompt_time(label):
    while True:
        value = _prompt_text(f"{label} (HH:MM)")
        try:
            datetime.strptime(value, "%H:%M")
            return value
        except ValueError:
            print("[Napaka] Uporabi obliko HH:MM.")


def _prompt_status():
    statuses = {"1": "scheduled", "2": "canceled", "3": "completed"}
    print("1. scheduled   2. canceled   3. completed")
    while True:
        choice = _prompt_text("Status")
        if choice in statuses:
            return statuses[choice]
        if choice in statuses.values():
            return choice
        print("[Napaka] Izberi 1, 2, 3 ali veljaven status.")


def _request(client, method, path, data=None, success_paths=(), success_text="Operacija uspešna"):
    """Pošlje obrazec ter preveri status HTTP in končni preusmeritveni naslov."""
    request_method = getattr(client, method.lower())
    response = request_method(path, data=data, follow_redirects=True)
    final_path = response.request.path
    if response.status_code >= 400 or (success_paths and final_path not in success_paths):
        print(f"\n[NEUSPEH] Zahteva ni bila izvedena (HTTP {response.status_code}, {final_path}).")
        details = clean_html(response.data)
        if details:
            print(details[:1200])
        return False
    print(f"\n[OK] {success_text}")
    return True


def _show(client, path, title):
    """Pridobi stran in izpiše vsebino brez navigacije in obrazcev."""
    response = client.get(path)
    _print_header(title)
    if response.status_code >= 400:
        print(f"[NEUSPEH] HTTP {response.status_code}")
        return
    print(clean_html(response.data) or "Ni podatkov.")


def admin_department_crud(client):
    while True:
        _print_header("ADMIN / ODDELKI")
        print("1. Ustvari   2. Preglej   3. Posodobi   4. Izbriši   0. Nazaj")
        choice = _prompt_text("Izbira")
        if choice == "1":
            _request(client, "post", "/add_department", {
                "name": _prompt_text("Ime oddelka"),
                "location": _prompt_text("Lokacija oddelka")
            }, ("/department_admin",), "Oddelek je ustvarjen.")
        elif choice == "2":
            _show(client, "/department_admin", "SEZNAM ODDELKOV")
        elif choice == "3":
            department_id = _prompt_int("ID oddelka")
            _request(client, "post", f"/update_department/{department_id}", {
                "department_name": _prompt_text("Novo ime"),
                "department_location": _prompt_text("Nova lokacija")
            }, ("/department_admin",), "Oddelek je posodobljen.")
        elif choice == "4":
            department_id = _prompt_int("ID oddelka")
            _request(client, "post", f"/delete_department/{department_id}", success_paths=("/department_admin",), success_text="Oddelek je izbrisan.")
        elif choice == "0":
            return
        else:
            print("[Napaka] Neveljavna izbira.")


def admin_staff_crud(client):
    while True:
        _print_header("ADMIN / ZAPOSLENI")
        print("1. Dodaj   2. Preglej   3. Posodobi   4. Izbriši   0. Nazaj")
        choice = _prompt_text("Izbira")
        if choice == "1":
            _request(client, "post", "/add_staff", {
                "name": _prompt_text("Ime in priimek"),
                "username": _prompt_text("Uporabniško ime"),
                "password": getpass("Geslo: "),
                "role": _prompt_text("Vloga (doctor/admin/patient)")
            }, ("/staff_admin",), "Zaposleni je dodan.")
        elif choice == "2":
            _show(client, "/staff_admin", "SEZNAM ZAPOSLENIH")
        elif choice == "3":
            staff_id = _prompt_int("ID zaposlenega")
            _request(client, "post", f"/update_staff/{staff_id}", {
                "name": _prompt_text("Ime in priimek"),
                "role": _prompt_text("Vloga (doctor/admin)"),
                "department_id": _prompt_int("ID oddelka")
            }, ("/staff_admin",), "Zaposleni je posodobljen.")
        elif choice == "4":
            staff_id = _prompt_int("ID zaposlenega")
            _request(client, "post", f"/delete_staff/{staff_id}", success_paths=("/staff_admin",), success_text="Zaposleni je izbrisan.")
        elif choice == "0":
            return
        else:
            print("[Napaka] Neveljavna izbira.")


def admin_menu(client):
    while True:
        _print_header("ADMINISTRATOR")
        print("1. Oddelki   2. Zaposleni   3. Pacienti")
        print("4. Pregledi  5. Sprejemi    6. Postelje")
        print("7. Sobe      8. Diagnoze    0. Odjava")
        choice = _prompt_text("Izbira")
        actions = {
            "1": lambda: admin_department_crud(client),
            "2": lambda: admin_staff_crud(client),
            "3": lambda: _show(client, "/patient_admin", "SEZNAM PACIENTOV"),
            "4": lambda: _show(client, "/appointment_admin", "SEZNAM PREGLEDOV"),
            "5": lambda: _show(client, "/admission_admin", "SEZNAM SPREJEMOV"),
            "6": lambda: _show(client, "/bed_admin", "SEZNAM POSTELJ"),
            "7": lambda: _show(client, "/room_admin", "SEZNAM SOB"),
            "8": lambda: _show(client, "/diagnosis_admin", "SEZNAM DIAGNOZ")
        }
        if choice == "0":
            return
        if choice in actions:
            actions[choice]()
        else:
            print("[Napaka] Neveljavna izbira.")


def doctor_menu(client):
    while True:
        _print_header("ZDRAVNIK")
        print("1. Pregledi       2. Dodaj pregled   3. Posodobi pregled")
        print("4. Sprejemi       5. Dodaj sprejem   0. Odjava")
        choice = _prompt_text("Izbira")
        if choice == "1":
            _show(client, "/appointment_doctor", "MOJI PREGLEDI")
        elif choice == "2":
            _request(client, "post", "/add_appointment", {
                "patient_id": _prompt_int("ID pacienta"),
                "appointment_date": _prompt_date("Datum pregleda"),
                "appointment_time": _prompt_time("Čas pregleda"),
                "status": _prompt_status()
            }, ("/appointment_doctor",), "Pregled je dodan.")
        elif choice == "3":
            appointment_id = _prompt_int("ID pregleda")
            _request(client, "post", f"/update_appointment/{appointment_id}", {
                "patient_id": _prompt_int("ID pacienta"),
                "appointment_date": _prompt_date("Datum pregleda"),
                "appointment_time": _prompt_time("Čas pregleda"),
                "status": _prompt_status()
            }, ("/appointment_doctor",), "Pregled je posodobljen.")
        elif choice == "4":
            _show(client, "/admission_doctor", "MOJI SPREJEMI")
        elif choice == "5":
            _request(client, "post", "/add_admission", {
                "patient_id": _prompt_int("ID pacienta"),
                "bed_id": _prompt_int("ID proste postelje"),
                "admission_date": _prompt_date("Datum sprejema")
            }, ("/admission_doctor",), "Sprejem je dodan.")
        elif choice == "0":
            return
        else:
            print("[Napaka] Neveljavna izbira.")


def patient_menu(client):
    while True:
        _print_header("PACIENT")
        print("1. Moji pregledi   0. Odjava")
        choice = _prompt_text("Izbira")
        if choice == "1":
            _show(client, "/appointment_patient", "MOJI PREGLEDI")
        elif choice == "0":
            return
        else:
            print("[Napaka] Neveljavna izbira.")


def run_terminal_interface():
    """Zažene tekstovni vmesnik prek testnega odjemalca Flaskove aplikacije."""
    with app.test_client() as client:
        _print_header("HOSPITAL DATABASE SYSTEM")
        username = _prompt_text("Uporabniško ime")
        password = getpass("Geslo: ")
        login_response = client.post("/auth/", data={
            "username": username,
            "password": password
        }, follow_redirects=True)

        final_path = login_response.request.path
        if final_path == "/auth/":
            print("\n[NEUSPEH] Napačno uporabniško ime ali geslo.")
            return

        print(f"\n[OK] Prijava uspešna. Vloga: {final_path.strip('/')}.")
        if final_path == "/admin":
            admin_menu(client)
        elif final_path == "/doctor":
            doctor_menu(client)
        elif final_path == "/patient":
            patient_menu(client)
        else:
            print("[NEUSPEH] Vloge ni bilo mogoče določiti.")
        client.get("/auth/logout")
        print("\n[OK] Odjava uspešna. Nasvidenje.")


if __name__ == "__main__":
    run_terminal_interface()