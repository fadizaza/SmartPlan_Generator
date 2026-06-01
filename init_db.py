"""
Initialize the database and create a default admin user.
Run this script once to set up the database.
"""
import os
from dotenv import load_dotenv
from app import app, db
from models import User

load_dotenv()

def init_db():
    with app.app_context():
        db.create_all()

        admin_password = os.getenv("ADMIN_PASSWORD", "password123")

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                name='Administrator',
                username='admin',
                email='admin@example.com'
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")

        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
