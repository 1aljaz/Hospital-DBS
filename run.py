from app import create_app
from flask_login import logout_user

app = create_app()
import atexit



# Ker je včasih ni logoutalo zadnjega uporabnika
atexit.register(logout_user)

if __name__ == "__main__":
    app.run(debug=True)