from app import db, create_app
from models import User,  News, Image

def create_tables():
    app = create_app('development')
    with app.app_context():
        # Create all tables
        db.create_all()
        print("All tables created successfully!")

if __name__ == "__main__":
    create_tables()
