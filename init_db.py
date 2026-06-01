"""
Initialize the database and create a default admin user.
Run this script once to set up the database.
"""
from app import app, db
from models import User

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user
            admin = User(
                name='Administrator',
                username='admin',
                email='admin@example.com'
            )
            admin.set_password('password123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
