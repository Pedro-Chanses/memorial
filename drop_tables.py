from app import db
from flask import Flask
from config import config

def drop_tables():
    app = Flask(__name__)
    app.config.from_object(config['development'])
    db.init_app(app)
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("All tables dropped successfully!")

if __name__ == "__main__":
    drop_tables()
